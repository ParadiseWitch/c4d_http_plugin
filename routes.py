# -*- coding: utf-8 -*-
"""
Route configuration and action handlers.
Extend ROUTES/ACTIONS to add new endpoints without touching server/tasks.
"""

import c4d
import os
from c4d import documents
import utils

# Path -> action name
ROUTES = {
    "/ping": "ping",
    "/show_joint": "show_joint",
    "/show_polygon": "show_polygon",
    "/open_project": "open_project",
}


def resolve_action(path):
    """Return the action string for a URL path or None if not found."""
    return ROUTES.get(path)


# Action handlers run on C4D main thread (invoked by tasks.process_tasks)
def _act_ping(payload=None):
    return "pong"


def _act_show_joint(payload=None):
    is_show = None
    if payload and isinstance(payload, dict):
        is_show = utils._as_bool(payload.get("isShow"), None)
    if is_show is None:
        # default to show if not provided
        is_show = True
    utils.set_joint_visibility(c4d.OBJECT_ON if is_show else c4d.OBJECT_OFF)
    return {"ok": True, "visible": bool(is_show)}


def _act_show_polygon(payload=None):
    is_show = None
    if payload and isinstance(payload, dict):
        is_show = utils._as_bool(payload.get("isShow"), None)
    if is_show is None:
        is_show = True
    utils.set_polygon_visibility(c4d.OBJECT_ON if is_show else c4d.OBJECT_OFF)
    return {"ok": True, "visible": bool(is_show)}


def _act_open_project(payload=None):
    p = None
    if payload and isinstance(payload, dict):
        p = payload.get("path")
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


# Action name -> callable
ACTIONS = {
    "ping": _act_ping,
    "show_joint": _act_show_joint,
    "show_polygon": _act_show_polygon,
    "open_project": _act_open_project,
}
