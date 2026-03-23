# -*- coding: utf-8 -*-
"""当前 HTTP 服务实例的运行时共享状态模块。"""

_current_http = None


def set_current_http(http_server):
    """保存当前已初始化的 HTTP 服务实例。"""
    global _current_http
    _current_http = http_server


def get_current_http():
    """返回当前保存的 HTTP 服务实例。"""
    return _current_http
