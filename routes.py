# -*- coding: utf-8 -*-
"""
Route configuration and action handlers.
Plugin layer only registers business handlers here.
"""

import c4d
import json
import os
from c4d import documents
import utils


def register(http_server):
    http_server.route("ping", handle_ping)
    http_server.route("get_joint", handle_get_joint)
    http_server.route("get_animation", handle_get_animation)
    http_server.route("show_joint", handle_show_joint)
    http_server.route("filter_joint", handle_filter_joint)
    http_server.route("show_polygon", handle_show_polygon)
    http_server.route("filter_polygon", handle_filter_polygon)
    http_server.route("open_project", handle_open_project)
    http_server.route("set_display_mode", handle_set_display_mode)
    http_server.route("select_weight_tag", handle_select_weight_tag)
    http_server.route("set_layout", handle_set_layout)


def handle_ping():
    return json.dumps({"status": True, "data": {"msg": "pong"}})


def handle_get_joint(request=None):
    joints = utils.get_all_joints()
    return {"ok": True, "hasJoint": bool(joints)}


def handle_get_animation(request=None):
    return {"ok": True, "hasAnimation": utils.has_animation()}


def handle_show_joint(request=None):
    is_show = True
    if request is not None:
        is_show = utils._as_bool(request.get_param("isShow"), True)
    utils.set_joint_visibility(c4d.OBJECT_ON if is_show else c4d.OBJECT_OFF)
    return {"ok": True, "visible": bool(is_show)}


def handle_show_polygon(request=None):
    is_show = True
    if request is not None:
        is_show = utils._as_bool(request.get_param("isShow"), True)
    utils.set_polygon_visibility(c4d.OBJECT_ON if is_show else c4d.OBJECT_OFF)
    return {"ok": True, "visible": bool(is_show)}


def handle_filter_joint(request=None):
    is_show = True
    if request is not None:
        is_show = utils._as_bool(request.get_param("isShow"), True)
    utils.enabel_joint_display_filter(is_show)
    return {"ok": True, "visible": bool(is_show)}


def handle_filter_polygon(request=None):
    is_show = True
    if request is not None:
        is_show = utils._as_bool(request.get_param("isShow"), True)
    utils.enabel_polygon_display_filter(is_show)
    return {"ok": True, "visible": bool(is_show)}


def handle_open_project(request=None):
    p = request.get_param("path") if request is not None else None
    if not p:
        return {"ok": False, "error": "missing-path"}
    try:
        p = os.path.expanduser(p)
        p = os.path.normpath(p)
    except Exception:
        pass
    if not os.path.isfile(p):
        return {"ok": False, "error": "not-found", "path": p}

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
            "SCENEFILTER_DIALOGSALLOWED",
        ):
            flags |= getattr(c4d, name, 0)

    doc = documents.LoadDocument(p, flags)
    if doc is None:
        return {"ok": False, "error": "load-failed", "path": p}

    prev = documents.GetActiveDocument()
    documents.InsertBaseDocument(doc)
    documents.SetActiveDocument(doc)
    c4d.EventAdd()
    try:
        if prev and prev != doc:
            documents.KillDocument(prev)
    except Exception:
        pass
    return {"ok": True, "opened": p}


def handle_set_display_mode(request=None):
    display_mode = request.get_param("displayMode") if request is not None else None
    if not display_mode:
        return {
            "ok": False,
            "error": "missing-display-mode",
        }
    try:
        mode = utils.set_active_view_display_mode(display_mode)
    except ValueError:
        return {
            "ok": False,
            "error": "unsupported-display-mode",
            "displayMode": display_mode,
            "supportedDisplayModes": sorted(utils.DISPLAY_MODE_MAP.keys()),
        }
    except RuntimeError as exc:
        return {
            "ok": False,
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": "set-display-mode-failed",
            "displayMode": display_mode,
            "message": str(exc),
        }
    return {"ok": True, "displayMode": mode}


def handle_select_weight_tag(request=None):
    is_select = True
    if request is not None:
        is_select = utils._as_bool(request.get_param("isSelect"), False)
    utils.select_all_weight_tags(is_select)
    return {"ok": True}


def handle_set_layout(request=None):
    layout_name = request.get_param("layoutName") if request is not None else None
    if not layout_name:
        return {"ok": False, "error": "missing-layout-name"}
    try:
        layout_path = utils.set_layout(layout_name)
    except IOError:
        return {"ok": False, "error": "layout-not-found", "layoutName": layout_name}
    except Exception as exc:
        return {
            "ok": False,
            "error": "load-layout-exception",
            "layoutName": layout_name,
            "message": str(exc),
        }
    return {"ok": True, "layoutName": layout_name, "layoutPath": layout_path}
