# -*- coding: utf-8 -*-
import c4d
from c4d import plugins

from constants import COMMAND_PLUGIN_ID, MESSAGE_PLUGIN_ID
import server
import tasks


class HttpControlCommand(plugins.CommandData):
    def __init__(self):
        self.running = server.is_server_running()

    def Execute(self, doc):
        self.running = server.is_server_running()
        if self.running:
            if server.stop_server():
                self.running = False
        else:
            if server.start_server():
                self.running = True
        return True

    def RestoreLayout(self, sec_ref):
        return True


class HttpControlMessage(plugins.MessageData):
    def CoreMessage(self, mid, bc):
        # Be robust across versions: always attempt to drain tasks.
        tasks.process_tasks()
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

    server.start_server()
