# -*- coding: utf-8 -*-
"""路由配置与业务处理函数模块。"""

import sys

import utils


if not hasattr(sys, "maxint"):
    sys.maxint = sys.maxsize


def register(http_server):
    """注册所有对外暴露的 HTTP 路由。"""
    http_server.route("open_project", handle_open_project)
    http_server.route("set_layout", handle_set_layout)
    http_server.route("has_joint", handle_has_joint)
    http_server.route("has_animation", handle_has_animation)
    http_server.route("set_display_mode", handle_set_display_mode)
    http_server.route("show_joint", handle_show_joint)
    http_server.route("show_polygon", handle_show_polygon)
    http_server.route("show_weight", handle_show_weight)
    http_server.route("go_to_start", handle_go_to_start)
    http_server.route("play", handle_play)
    http_server.route("is_playing", handle_is_playing)


def succ(data=None):
    """生成统一的成功返回结构。"""
    return {"status": "succ", "data": data or {}}


def erro(msg):
    """生成统一的失败返回结构。"""
    return {"status": "erro", "msg": msg}


def handle_open_project(request=None):
    """打开指定路径的工程文件并切换为当前活动文档。"""
    p = request.get_param("path") if request is not None else None
    if not p:
        return erro("缺少工程文件路径参数 path")
    try:
        return succ(utils.open_project(p))
    except Exception as exc:
        return erro(str(exc))


def handle_set_layout(request=None):
    """按名称或路径加载并切换 Cinema 4D 布局文件。"""
    layout_name = request.get_param("layoutName") if request is not None else None
    if not layout_name:
        return erro("缺少布局名称参数 layoutName")
    try:
        return succ(utils.set_layout(layout_name))
    except Exception as exc:
        return erro(str(exc))


def handle_set_display_mode(request=None):
    """设置当前激活视图的显示模式。"""
    display_mode = request.get_param("displayMode") if request is not None else None
    if not display_mode:
        return erro("缺少显示模式参数 displayMode")
    try:
        return succ(utils.set_active_view_display_mode(display_mode))
    except Exception as exc:
        return erro(str(exc))


def handle_has_joint(request=None):
    """查询当前文档中是否存在关节或骨骼对象。"""
    try:
        return succ({"hasJoint": bool(utils.get_all_joints())})
    except Exception as exc:
        return erro(str(exc))


def handle_has_animation(request=None):
    """查询当前文档是否包含动画数据。"""
    try:
        return succ({"hasAnimation": utils.has_animation()})
    except Exception as exc:
        return erro(str(exc))


def handle_show_joint(request=None):
    """控制当前文档中所有关节对象在编辑器中的显示状态。"""
    is_show = request.get_param("isShow") if request is not None else True
    try:
        return succ(utils.show_joint(is_show))
    except Exception as exc:
        return erro(str(exc))


def handle_show_polygon(request=None):
    """控制当前文档中所有多边形对象在编辑器中的显示状态。"""
    is_show = request.get_param("isShow") if request is not None else True
    try:
        return succ(utils.show_polygon(is_show))
    except Exception as exc:
        return erro(str(exc))


def handle_show_weight(request=None):
    """控制当前文档中权重相关标签的选中状态。"""
    is_show = request.get_param("isShow") if request is not None else False
    try:
        return succ(utils.show_weight(is_show))
    except Exception as exc:
        return erro(str(exc))


def handle_go_to_start(request=None):
    """将当前活动文档跳转到起始帧。"""
    try:
        return succ(utils.go_to_start())
    except Exception as exc:
        return erro(str(exc))


def handle_play(request=None):
    """跳转到第一帧并开始单次播放。"""
    try:
        return succ(utils.play_once_from_start())
    except Exception as exc:
        return erro(str(exc))


def handle_is_playing(request=None):
    """查询当前工程的是否正在播放。"""
    try:
        return succ(utils.is_playing())
    except Exception as exc:
        return erro(str(exc))
