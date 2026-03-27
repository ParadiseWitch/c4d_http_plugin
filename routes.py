# -*- coding: utf-8 -*-
"""
路由配置与业务处理函数模块。

插件层仅在此处注册业务路由与对应的处理逻辑。
"""

import c4d
import json
import os
import sys
from c4d import documents
import utils


if not hasattr(sys, "maxint"):
    sys.maxint = sys.maxsize


def register(http_server):
    """注册所有对外暴露的 HTTP 路由。"""
    http_server.route("ping", handle_ping)
    http_server.route("open_project", handle_open_project)
    http_server.route("set_display_mode", handle_set_display_mode)
    http_server.route("set_view_clipping", handle_set_view_clipping)
    http_server.route("show_joint", handle_show_joint)
    http_server.route("show_polygon", handle_show_polygon)
    http_server.route("show_weight", handle_show_weight)
    http_server.route("set_layout", handle_set_layout)
    http_server.route("center_model", handle_center_model)
    http_server.route("get_joint", handle_get_joint)
    http_server.route("get_animation", handle_get_animation)
    http_server.route("play", handle_play)
    http_server.route("is_playing", handle_is_playing)


def succ(data=None):
    """生成统一的成功返回结构。"""
    return {"status": "succ", "data": data or {}}


def erro(msg):
    """生成统一的失败返回结构。"""
    return {"status": "erro", "msg": msg}


def handle_ping():
    """返回服务健康检查结果。"""
    return json.dumps(succ({"msg": "pong"}), ensure_ascii=False)


def handle_open_project(request=None):
    """打开指定路径的工程文件并切换为当前活动文档。"""
    p = request.get_param("path") if request is not None else None
    if not p:
        return erro("缺少工程文件路径参数 path")
    try:
        p = os.path.expanduser(p)
        p = os.path.normpath(p)
    except Exception:
        pass
    if not os.path.isfile(p):
        return erro("工程文件不存在: %s" % p)

    flags = getattr(c4d, "SCENEFILTER_ALL", 0)
    if not flags:
        for name in (
            "SCENEFILTER_OBJECTS",
            "SCENEFILTER_MATERIALS",
            "SCENEFILTER_SHADERS",
            "SCENEFILTER_EXPRESSIONS",
            "SCENEFILTER_TIMELINE",
            "SCENEFILTER_PARTICLES",
            "SCENEFILTER_OTHER",
            "SCENEFILTER_ANIMATION",
            # "SCENEFILTER_DIALOGSALLOWED",
        ):
            flags |= getattr(c4d, name, 0)

    doc = documents.LoadDocument(p, flags)
    if doc is None:
        return erro("工程文件加载失败: %s" % p)

    prev = documents.GetActiveDocument()
    documents.InsertBaseDocument(doc)
    documents.SetActiveDocument(doc)
    utils.set_active_view_clipping()
    try:
        if prev and prev != doc:
            documents.KillDocument(prev)
    except Exception:
        pass
    return succ({"opened": p})


def handle_set_display_mode(request=None):
    """设置当前激活视图的显示模式。"""
    display_mode = request.get_param("displayMode") if request is not None else None
    if not display_mode:
        return erro("缺少显示模式参数 displayMode")
    try:
        mode = utils.set_active_view_display_mode(display_mode)
    except ValueError:
        return erro(
            "不支持的显示模式: %s，可选值为: %s"
            % (display_mode, "、".join(sorted(utils.DISPLAY_MODE_MAP.keys())))
        )
    except Exception as exc:
        return erro(str(exc))
    return succ({"displayMode": mode, "displayModeName": display_mode})


def handle_set_view_clipping(request=None):
    """设置当前活动视图的近裁剪与远裁剪范围。"""
    near = 0
    far = sys.maxint
    if request is not None:
        near = request.get_param("nearCm")
        far = request.get_param("farCm")

    try:
        result = utils.set_active_view_clipping(near, far)
    except ValueError as exc:
        return erro(str(exc))
    except Exception as exc:
        return erro(str(exc))
    return succ(result)


def handle_show_joint(request=None):
    """控制当前文档中所有关节对象在编辑器中的显示状态。"""
    is_show = True
    if request is not None:
        is_show = utils._as_bool(request.get_param("isShow"), True)
    utils.set_joint_visibility(c4d.OBJECT_ON if is_show else c4d.OBJECT_OFF)
    utils.enabel_joint_display_filter(is_show)
    return succ({"visible": bool(is_show)})


def handle_show_polygon(request=None):
    """控制当前文档中所有多边形对象在编辑器中的显示状态。"""
    is_show = True
    if request is not None:
        is_show = utils._as_bool(request.get_param("isShow"), True)
    utils.set_polygon_visibility(c4d.OBJECT_ON if is_show else c4d.OBJECT_OFF)
    utils.enabel_polygon_display_filter(is_show)
    return succ({"visible": bool(is_show)})


def handle_show_weight(request=None):
    """显示权重影响"""
    is_show = True
    if request is not None:
        is_show = utils._as_bool(request.get_param("isSelect"), False)
    utils.select_all_weight_tags(is_show)
    return succ({"visible": bool(is_show)})


def handle_set_layout(request=None):
    """按名称或路径加载并切换 Cinema 4D 布局文件。"""
    layout_name = request.get_param("layoutName") if request is not None else None
    if not layout_name:
        return erro("缺少布局名称参数 layoutName")
    try:
        layout_path = utils.set_layout(layout_name)
    except IOError:
        return erro("未找到布局文件: %s" % layout_name)
    except Exception as exc:
        return erro("加载布局失败: %s" % str(exc))
    return succ({"layoutName": layout_name, "layoutPath": layout_path})


def handle_center_model(request=None):
    """若场景存在摄像机则切入摄像机视角，否则居中显示几何体模型。"""
    try:
        result = utils.center_model_in_active_view()
    except Exception as exc:
        return erro(str(exc))
    return succ(result)


def handle_get_joint(request=None):
    """查询当前文档中是否存在关节或骨骼对象。"""
    joints = utils.get_all_joints()
    return succ({"hasJoint": bool(joints)})


def handle_get_animation(request=None):
    """查询当前文档是否包含动画数据。"""
    return succ(utils.get_animation_details())


def handle_play(request=None):
    """跳转到第一帧并开始单次播放。"""
    # 设置单次播放
    c4d.CallCommand(12426)
    # 跳转到第一帧
    c4d.CallCommand(12501)
    # 播放
    c4d.CallCommand(12412)
    return succ()


def handle_is_playing(request=None):
    """查询当前工程的是否正在播放。"""
    is_playing = c4d.IsCommandChecked(12412)
    return succ({"is_playing": is_playing})
