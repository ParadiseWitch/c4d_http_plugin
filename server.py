# -*- coding: utf-8 -*-
import threading
import json

# try:  # Python 2 (C4D R19)
import BaseHTTPServer as _httpserver
from BaseHTTPServer import BaseHTTPRequestHandler
import SocketServer as _socketserver
import urlparse as _urlparse
# except ImportError:  # Python 3
#     import http.server as _httpserver
#     from http.server import BaseHTTPRequestHandler
#     import socketserver as _socketserver
#     from urllib import parse as _urlparse

from constants import env_host_port
from tasks import enqueue_task
import routes

_server_thread = None
_httpd = None


def _respond(handler, code, body, content_type='text/plain; charset=utf-8'):
    try:
        if not isinstance(body, bytes):
            body = str(body).encode('utf-8')
        handler.send_response(code)
        handler.send_header('Content-Type', content_type)
        handler.send_header('Content-Length', str(len(body)))
        handler.send_header('Connection', 'close')
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        try:
            print('[http] respond error: %s' % e)
        except Exception:
            pass


class _RequestHandler(BaseHTTPRequestHandler):
    server_version = 'C4DHttpControl/1.0'

    def log_message(self, fmt, *args):
        try:
            print('[http] ' + (fmt % args))
        except Exception:
            pass

    def do_GET(self):
        try:
            parsed = _urlparse.urlparse(self.path)
            path = parsed.path or '/'
            try:
                qs = _urlparse.parse_qs(parsed.query) if parsed.query else {}
            except Exception:
                qs = {}

            if path == '/ping':
                _respond(self, 200, 'pong')
                return

            action = routes.resolve_action(path)
            if action:
                payload = {}
                if 'path' in qs and qs.get('path'):
                    try:
                        payload['path'] = qs['path'][0]
                    except Exception:
                        pass
                evt = threading.Event()
                task = {'action': action, 'payload': payload, 'event': evt, 'result': None, 'error': None}
                enqueue_task(task)
                evt.wait()
                body = json.dumps(task.get('result') or {'ok': True})
                _respond(self, 200, body, 'application/json; charset=utf-8')
                return

            _respond(self, 404, 'not found')
        except Exception as e:
            _respond(self, 500, 'error: %s' % e)


class _ThreadingHTTPServer(_socketserver.ThreadingMixIn, _httpserver.HTTPServer):
    daemon_threads = True


def start_server():
    global _server_thread, _httpd
    if _server_thread is not None:
        print('[http] server already running')
        return True
    host, port = env_host_port()
    try:
        _httpd = _ThreadingHTTPServer((host, port), _RequestHandler)
    except Exception as e:
        print('[http] bind failed %s:%s -> %s' % (host, port, e))
        _httpd = None
        return False

    def _serve():
        try:
            print('[http] serving on %s:%s' % (host, port))
            _httpd.serve_forever()
        except Exception as e:
            print('[http] server error: %s' % e)
        finally:
            try:
                _httpd.server_close()
            except Exception:
                pass
            print('[http] server stopped')

    _server_thread = threading.Thread(target=_serve)
    _server_thread.daemon = True
    _server_thread.start()
    return True


def stop_server():
    global _server_thread, _httpd
    if _server_thread is None or _httpd is None:
        print('[http] server not running')
        _server_thread = None
        _httpd = None
        return True
    try:
        _httpd.shutdown()
    except Exception as e:
        print('[http] shutdown error: %s' % e)
    try:
        _server_thread.join(2.0)
    except Exception:
        pass
    _server_thread = None
    _httpd = None
    return True
