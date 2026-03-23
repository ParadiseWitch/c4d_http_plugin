# -*- coding: utf-8 -*-
"""
Cinema 4D 插件入口与注册模块。

- `routes.py`：业务路由处理函数
- `http/`：可复用的 HTTP 服务与主线程任务调度
"""

import os
import sys

# 确保在 C4D R19 环境下可以导入当前插件目录中的同级模块。
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


# 正式发布时应替换为 Plug-in Cafe 分配的正式插件 ID。
COMMAND_PLUGIN_ID = 1070002  # 命令插件 ID：用于菜单启停。
MESSAGE_PLUGIN_ID = 1070003  # 消息插件 ID：用于处理主线程任务事件。

_http = None


def env_host_port():
    """读取环境变量中的 HTTP 服务监听地址与端口。"""
    host = os.environ.get("C4D_HTTP_HOST", "127.0.0.1")
    port_str = os.environ.get("C4D_HTTP_PORT", "8090")
    try:
        port = int(port_str)
    except Exception:
        port = 8090
    return host, port


def get_http():
    """获取并延迟初始化全局 HTTP 服务实例。"""
    global _http
    if _http is None:
        host, port = env_host_port()
        _http = Http(port=port, host=host, message_plugin_id=MESSAGE_PLUGIN_ID)
        routes.register(_http)
        set_current_http(_http)
    return _http


class HttpControlCommand(plugins.CommandData):
    """C4D 命令插件，用于在菜单中启动或停止 HTTP 服务。"""

    def __init__(self):
        """初始化命令插件并同步当前服务运行状态。"""
        self.running = get_http().is_running()

    def Execute(self, doc):
        """响应菜单点击事件，切换 HTTP 服务的启停状态。"""
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
        """恢复插件布局时返回成功，满足 C4D 插件接口要求。"""
        return True


class HttpControlMessage(plugins.MessageData):
    """C4D 消息插件，用于在主线程中处理排队的 HTTP 任务。"""

    def CoreMessage(self, mid, bc):
        """处理主线程消息并执行等待中的路由任务。"""
        get_http().process_tasks()
        return True


def register():
    """向 Cinema 4D 注册命令插件、消息插件并启动 HTTP 服务。"""
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
