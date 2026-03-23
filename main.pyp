# -*- coding: utf-8 -*-
"""
Cinema 4D plugin entry and registration:
- routes.py: business route handlers
- http/: reusable HTTP server and main-thread task dispatch
"""

import os
import sys

# Ensure this plugin folder is importable for sibling modules in C4D R19
try:
    _BASE_DIR = os.path.dirname(__file__)
except Exception:
    _BASE_DIR = os.getcwd()
if _BASE_DIR and _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

import c4d
from c4d import plugins

from http import Http, set_current_http
import routes


# Replace with official IDs from Plug-in Cafe for production
COMMAND_PLUGIN_ID = 1070002  # Command plugin: menu toggle
MESSAGE_PLUGIN_ID = 1070003  # Message plugin: processes SpecialEvent tasks

_http = None


def env_host_port():
    host = os.environ.get("C4D_HTTP_HOST", "127.0.0.1")
    port_str = os.environ.get("C4D_HTTP_PORT", "8090")
    try:
        port = int(port_str)
    except Exception:
        port = 8090
    return host, port


def get_http():
    global _http
    if _http is None:
        host, port = env_host_port()
        _http = Http(port=port, host=host, message_plugin_id=MESSAGE_PLUGIN_ID)
        routes.register(_http)
        set_current_http(_http)
    return _http


class HttpControlCommand(plugins.CommandData):
    def __init__(self):
        self.running = get_http().is_running()

    def Execute(self, doc):
        http_server = get_http()
        self.running = http_server.is_running()
        if self.running:
            if http_server.stop():
                self.running = False
        else:
            if http_server.start():
                self.running = True
        return True

    def RestoreLayout(self, sec_ref):
        return True


class HttpControlMessage(plugins.MessageData):
    def CoreMessage(self, mid, bc):
        get_http().process_tasks()
        return True


def register():
    plugins.RegisterCommandPlugin(
        id=COMMAND_PLUGIN_ID,
        str="HTTP Control: Start/Stop",
        info=0,
        icon=None,
        help="启动/停止 HTTP 服务器以控制 C4D 路由",
        dat=HttpControlCommand(),
    )

    plugins.RegisterMessagePlugin(
        id=MESSAGE_PLUGIN_ID,
        str="HTTP Control Events",
        info=0,
        dat=HttpControlMessage(),
    )

    get_http().start()


if __name__ == "__main__":
    register()
