# -*- coding: utf-8 -*-

_current_http = None


def set_current_http(http_server):
    global _current_http
    _current_http = http_server


def get_current_http():
    return _current_http
