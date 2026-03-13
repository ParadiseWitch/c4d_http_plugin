# -*- coding: utf-8 -*-
import c4d
from c4d import documents


def iter_objects(root):
    """Depth-first traversal starting from root object."""
    op = root
    while op:
        yield op
        child = op.GetDown()
        if child:
            for x in iter_objects(child):
                yield x
        op = op.GetNext()


def get_all_objects(doc=None):
    """Return a list of all objects in the active document (or given doc)."""
    doc = documents.GetActiveDocument()
    if doc is None:
        return []
    res = []
    roots = doc.GetObjects()

    for r in roots:
        for obj in iter_objects(r):
            res.append(obj)
    return res


def find_objects_by_types(type_ids, doc=None):
    """Return objects whose type matches any id in type_ids.

    type_ids: iterable of integer type IDs (e.g., c4d.Ojoint, c4d.Opolygon)
    """
    objs = get_all_objects(doc)
    matched = []
    for obj in objs:
        try:
            for tid in type_ids:
                if tid and obj.CheckType(tid):
                    matched.append(obj)
                    break
        except Exception:
            pass
    return matched


def get_all_joints(doc=None):
    return find_objects_by_types(
        (getattr(c4d, "Ojoint", 0), getattr(c4d, "Obone", 0)), doc
    )


def get_all_polygons(doc=None):
    return find_objects_by_types((getattr(c4d, "Opolygon", 0),), doc)


def set_joint_visibility(value, doc=None):
    if doc is None:
        doc = documents.GetActiveDocument()
    for obj in get_all_joints(doc):
        try:
            obj[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = value
        except Exception:
            pass
    c4d.EventAdd()


def set_polygon_visibility(value, doc=None):
    if doc is None:
        doc = documents.GetActiveDocument()
    for obj in get_all_polygons(doc):
        try:
            obj[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = value
        except Exception:
            pass
    c4d.EventAdd()
