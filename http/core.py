# -*- coding: utf-8 -*-
"""HTTP 服务核心模块，负责请求分发与主线程任务调度。"""

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
    """封装 HTTP 请求路径与查询参数，便于业务层读取。"""

    def __init__(self, path, query=None):
        """根据请求路径和查询参数初始化请求对象。"""
        self.path = path or "/"
        self.query = query or {}
        self.params = {}
        for key, value in self.query.items():
            if isinstance(value, (list, tuple)):
                self.params[key] = value[0] if value else None
            else:
                self.params[key] = value

    def get_param(self, key, default=None):
        """读取单个查询参数，不存在时返回默认值。"""
        value = self.params.get(key)
        if value is None:
            return default
        return value


class _MainThreadTaskRunner(object):
    """将 HTTP 请求包装为任务并投递到 C4D 主线程执行。"""

    def __init__(self, message_plugin_id):
        """初始化任务队列与对应的消息插件 ID。"""
        self._message_plugin_id = message_plugin_id
        self._queue = _queue.Queue()

    def enqueue(self, task):
        """将任务加入队列并触发一次主线程消息。"""
        self._queue.put(task)
        c4d.SpecialEventAdd(self._message_plugin_id)

    def process_tasks(self, invoke_handler):
        """在主线程中逐个执行排队任务并回填结果。"""
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
                result = {"status": "erro", "msg": "路由处理执行失败"}

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
                print("[http] 已处理 %d 个任务" % processed)
            except Exception:
                pass


class _ThreadingHTTPServer(_socketserver.ThreadingMixIn, _httpserver.HTTPServer):
    """支持多线程处理连接的 HTTP 服务器。"""

    daemon_threads = True


class Http(object):
    """对外提供路由注册、服务启停与请求处理能力的 HTTP 服务类。"""

    def __init__(self, port, host="127.0.0.1", message_plugin_id=None):
        """初始化 HTTP 服务配置与主线程任务调度器。"""
        if message_plugin_id is None:
            raise ValueError("message_plugin_id is required")
        self.host = host
        self.port = port
        self._routes = {}
        self._server_thread = None
        self._httpd = None
        self._task_runner = _MainThreadTaskRunner(message_plugin_id)

    def route(self, path, handler):
        """注册单个业务路由及其处理函数。"""
        if not path:
            raise ValueError("path is required")
        normalized = "/" + path.lstrip("/")
        self._routes[normalized] = handler
        return handler

    def enqueue_task(self, task):
        """向主线程任务队列中压入一个待执行任务。"""
        self._task_runner.enqueue(task)

    def process_tasks(self):
        """处理当前排队的全部主线程任务。"""
        self._task_runner.process_tasks(self._invoke_handler)

    def is_running(self):
        """判断 HTTP 服务线程与服务实例是否处于运行状态。"""
        return self._server_thread is not None and self._httpd is not None

    def start(self):
        """启动 HTTP 服务并创建后台监听线程。"""
        if self.is_running():
            print("[http] 服务已在运行中")
            return True

        try:
            self._httpd = _ThreadingHTTPServer(
                (self.host, self.port), self._build_request_handler()
            )
        except Exception as exc:
            print("[http] 绑定失败 %s:%s -> %s" % (self.host, self.port, exc))
            self._httpd = None
            return False

        def _serve():
            """后台线程入口，持续处理传入的 HTTP 请求。"""
            try:
                print("[http] 服务启动于 %s:%s" % (self.host, self.port))
                self._httpd.serve_forever()
            except Exception as exc:
                print("[http] 服务运行错误: %s" % exc)
            finally:
                try:
                    self._httpd.server_close()
                except Exception:
                    pass
                print("[http] 服务已停止")

        self._server_thread = threading.Thread(target=_serve)
        self._server_thread.daemon = True
        self._server_thread.start()
        return True

    def stop(self):
        """停止 HTTP 服务并等待后台线程退出。"""
        if not self.is_running():
            print("[http] 服务当前未运行")
            self._server_thread = None
            self._httpd = None
            return True

        try:
            self._httpd.shutdown()
        except Exception as exc:
            print("[http] 停止服务时出错: %s" % exc)

        try:
            self._server_thread.join(2.0)
        except Exception:
            pass

        self._server_thread = None
        self._httpd = None
        return True

    def _build_request_handler(self):
        """构建绑定到当前服务实例的请求处理类。"""
        http_server = self

        class _RequestHandler(BaseHTTPRequestHandler):
            """标准库请求处理器，负责接收并转发 GET 请求。"""

            server_version = "C4DHttpControl/1.0"

            def log_message(self, fmt, *args):
                """将 HTTP 访问日志输出到 C4D 控制台。"""
                try:
                    print("[http] " + (fmt % args))
                except Exception:
                    pass

            def do_GET(self):
                """处理 GET 请求并转交到业务路由。"""
                http_server._handle_get(self)

        return _RequestHandler

    def _handle_get(self, handler):
        """解析 GET 请求、调度主线程执行并回写响应。"""
        try:
            parsed = _urlparse.urlparse(handler.path)
            path = parsed.path or "/"
            query = _urlparse.parse_qs(parsed.query) if parsed.query else {}
            route_handler = self._routes.get(path)
            if route_handler is None:
                self._respond_json(handler, 404, {"status": "erro", "msg": "请求的路由不存在"})
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
            self._respond_json(handler, 500, {"status": "erro", "msg": "处理请求失败: %s" % exc})

    def _write_result(self, handler, result):
        """将路由结果规范化为统一 JSON 结构后输出。"""
        normalized = self._normalize_result(result)
        self._respond_json(handler, 200, normalized)

    def _normalize_result(self, result):
        """把路由返回值规范化为统一的中文 JSON 返回结构。"""
        if result is None:
            return {"status": "succ", "data": {}}

        try:
            string_types = (basestring,)
        except Exception:
            string_types = (str, bytes)

        if isinstance(result, string_types):
            try:
                parsed = json.loads(result)
            except Exception:
                return {"status": "succ", "data": {"text": result}}
            return self._normalize_result(parsed)

        if isinstance(result, dict):
            status = result.get("status")
            if status == "succ":
                return {"status": "succ", "data": result.get("data") or {}}
            if status == "erro":
                return {"status": "erro", "msg": result.get("msg") or "请求处理失败"}

            if result.get("ok") is True:
                data = dict(result)
                data.pop("ok", None)
                data.pop("error", None)
                data.pop("message", None)
                return {"status": "succ", "data": data}

            if result.get("ok") is False:
                msg = result.get("message") or result.get("error") or "请求处理失败"
                return {"status": "erro", "msg": msg}

            return {"status": "succ", "data": result}

        return {"status": "succ", "data": {"value": result}}

    def _respond_json(self, handler, code, payload):
        """按 UTF-8 JSON 格式输出响应内容。"""
        body = json.dumps(payload, ensure_ascii=False)
        self._respond(handler, code, body, "application/json; charset=utf-8")

    def _respond(self, handler, code, body, content_type="text/plain; charset=utf-8"):
        """将指定内容写入 HTTP 响应。"""
        try:
            try:
                unicode_type = unicode
            except Exception:
                unicode_type = str

            if isinstance(body, unicode_type):
                body = body.encode("utf-8")
            elif not isinstance(body, bytes):
                body = str(body).encode("utf-8")
            handler.send_response(code)
            handler.send_header("Content-Type", content_type)
            handler.send_header("Content-Length", str(len(body)))
            handler.send_header("Connection", "close")
            handler.end_headers()
            handler.wfile.write(body)
        except Exception as exc:
            try:
                print("[http] 响应输出失败: %s" % exc)
            except Exception:
                pass

    def _invoke_handler(self, route_handler, request):
        """根据处理函数签名决定是否向其传入请求对象。"""
        if route_handler is None:
            return {"status": "erro", "msg": "缺少路由处理函数"}

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
