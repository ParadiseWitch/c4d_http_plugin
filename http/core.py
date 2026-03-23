# -*- coding: utf-8 -*-
import inspect
import json
import threading
import traceback

import c4d
import BaseHTTPServer as _httpserver
from BaseHTTPServer import BaseHTTPRequestHandler
import Queue as _queue
import SocketServer as _socketserver
import urlparse as _urlparse


class HttpRequest(object):
    def __init__(self, path, query=None):
        self.path = path or "/"
        self.query = query or {}
        self.params = {}
        for key, value in self.query.items():
            if isinstance(value, (list, tuple)):
                self.params[key] = value[0] if value else None
            else:
                self.params[key] = value

    def get_param(self, key, default=None):
        value = self.params.get(key)
        if value is None:
            return default
        return value


class _MainThreadTaskRunner(object):
    def __init__(self, message_plugin_id):
        self._message_plugin_id = message_plugin_id
        self._queue = _queue.Queue()

    def enqueue(self, task):
        self._queue.put(task)
        c4d.SpecialEventAdd(self._message_plugin_id)

    def process_tasks(self, invoke_handler):
        processed = 0
        while True:
            try:
                task = self._queue.get_nowait()
            except Exception:
                break

            result = None
            try:
                result = invoke_handler(task.get("handler"), task.get("request"))
            except Exception:
                stack = traceback.format_exc()
                print(stack)
                result = {"ok": False, "error": "handler-failed", "stack": stack}

            task["result"] = result
            event = task.get("event")
            if event is not None:
                try:
                    event.set()
                except Exception:
                    pass
            processed += 1

        if processed:
            try:
                print("[http] processed %d task(s)" % processed)
            except Exception:
                pass


class _ThreadingHTTPServer(_socketserver.ThreadingMixIn, _httpserver.HTTPServer):
    daemon_threads = True


class Http(object):
    def __init__(self, port, host="127.0.0.1", message_plugin_id=None):
        if message_plugin_id is None:
            raise ValueError("message_plugin_id is required")
        self.host = host
        self.port = port
        self._routes = {}
        self._server_thread = None
        self._httpd = None
        self._task_runner = _MainThreadTaskRunner(message_plugin_id)

    def route(self, path, handler):
        if not path:
            raise ValueError("path is required")
        normalized = "/" + path.lstrip("/")
        self._routes[normalized] = handler
        return handler

    def enqueue_task(self, task):
        self._task_runner.enqueue(task)

    def process_tasks(self):
        self._task_runner.process_tasks(self._invoke_handler)

    def is_running(self):
        return self._server_thread is not None and self._httpd is not None

    def start(self):
        if self.is_running():
            print("[http] server already running")
            return True

        try:
            self._httpd = _ThreadingHTTPServer(
                (self.host, self.port), self._build_request_handler()
            )
        except Exception as exc:
            print("[http] bind failed %s:%s -> %s" % (self.host, self.port, exc))
            self._httpd = None
            return False

        def _serve():
            try:
                print("[http] serving on %s:%s" % (self.host, self.port))
                self._httpd.serve_forever()
            except Exception as exc:
                print("[http] server error: %s" % exc)
            finally:
                try:
                    self._httpd.server_close()
                except Exception:
                    pass
                print("[http] server stopped")

        self._server_thread = threading.Thread(target=_serve)
        self._server_thread.daemon = True
        self._server_thread.start()
        return True

    def stop(self):
        if not self.is_running():
            print("[http] server not running")
            self._server_thread = None
            self._httpd = None
            return True

        try:
            self._httpd.shutdown()
        except Exception as exc:
            print("[http] shutdown error: %s" % exc)

        try:
            self._server_thread.join(2.0)
        except Exception:
            pass

        self._server_thread = None
        self._httpd = None
        return True

    def _build_request_handler(self):
        http_server = self

        class _RequestHandler(BaseHTTPRequestHandler):
            server_version = "C4DHttpControl/1.0"

            def log_message(self, fmt, *args):
                try:
                    print("[http] " + (fmt % args))
                except Exception:
                    pass

            def do_GET(self):
                http_server._handle_get(self)

        return _RequestHandler

    def _handle_get(self, handler):
        try:
            parsed = _urlparse.urlparse(handler.path)
            path = parsed.path or "/"
            query = _urlparse.parse_qs(parsed.query) if parsed.query else {}
            route_handler = self._routes.get(path)
            if route_handler is None:
                self._respond(handler, 404, "not found")
                return

            request = HttpRequest(path, query)
            event = threading.Event()
            task = {
                "handler": route_handler,
                "request": request,
                "event": event,
                "result": None,
            }
            self._task_runner.enqueue(task)
            event.wait()
            self._write_result(handler, task.get("result"))
        except Exception as exc:
            self._respond(handler, 500, "error: %s" % exc)

    def _write_result(self, handler, result):
        content_type = "application/json; charset=utf-8"
        body = result

        try:
            string_types = (basestring,)
        except Exception:
            string_types = (str, bytes)

        if isinstance(result, string_types):
            content_type = self._guess_content_type(result)
        else:
            body = json.dumps(result or {"ok": True})

        self._respond(handler, 200, body, content_type)

    def _guess_content_type(self, result):
        try:
            text = result.strip()
        except Exception:
            return "text/plain; charset=utf-8"
        if text.startswith("{") or text.startswith("["):
            return "application/json; charset=utf-8"
        return "text/plain; charset=utf-8"

    def _respond(self, handler, code, body, content_type="text/plain; charset=utf-8"):
        try:
            if not isinstance(body, bytes):
                body = str(body).encode("utf-8")
            handler.send_response(code)
            handler.send_header("Content-Type", content_type)
            handler.send_header("Content-Length", str(len(body)))
            handler.send_header("Connection", "close")
            handler.end_headers()
            handler.wfile.write(body)
        except Exception as exc:
            try:
                print("[http] respond error: %s" % exc)
            except Exception:
                pass

    def _invoke_handler(self, route_handler, request):
        if route_handler is None:
            return {"ok": False, "error": "missing-handler"}

        try:
            argspec = inspect.getargspec(route_handler)
            arg_count = len(argspec.args or [])
            if inspect.ismethod(route_handler):
                try:
                    if route_handler.im_self is not None:
                        arg_count -= 1
                except Exception:
                    pass
            has_varargs = bool(argspec.varargs)
        except Exception:
            arg_count = 1
            has_varargs = False

        if has_varargs or arg_count > 0:
            return route_handler(request)
        return route_handler()
