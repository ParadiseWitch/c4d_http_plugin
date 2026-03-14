# -*- coding: utf-8 -*-
import c4d
from c4d import documents


# Action handlers run on C4D main thread (invoked by tasks.process_tasks)
def _as_bool(val, default=None):
    try:
        if isinstance(val, bool):
            return val
        s = str(val).strip().lower()
        if s in ("1", "true", "yes", "on"):
            return True
        if s in ("0", "false", "no", "off"):
            return False
    except Exception:
        pass
    return default


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


def enabel_joint_display_filter(value):
    doc = documents.GetActiveDocument()
    bd = doc.GetActiveBaseDraw()
    # 关闭 Joint 显示
    bd[c4d.BASEDRAW_DISPLAYFILTER_JOINT] = value
    c4d.EventAdd()


def enabel_polygon_display_filter(value):
    doc = documents.GetActiveDocument()
    bd = doc.GetActiveBaseDraw()
    # 关闭 多边形 显示
    bd[c4d.BASEDRAW_DISPLAYFILTER_POLYGON] = value
    bd[c4d.BASEDRAW_DISPLAYFILTER_SPLINE] = value
    bd[c4d.BASEDRAW_DISPLAYFILTER_GENERATOR] = value
    bd[c4d.DISPLAYFILTER_HYPERNURBS] = value
    bd[c4d.DISPLAYFILTER_MULTIAXIS] = value

    c4d.EventAdd()


def select_all_weight_tags(clear_existing=False):
    """Select all weight-related tags in the document.

    This targets C4D's Weight tag (joint weights) and Vertex Map tag, as
    both are commonly referred to as "权重标签" in workflows.

    Args:
        doc: Optional c4d.BaseDocument. Defaults to active document.
        clear_existing: If True, deselects all tags first.

    Returns:
        int: Number of tags that were selected.
    """
    doc = documents.GetActiveDocument()
    if doc is None:
        return 0

    # Collect candidate tag type IDs (skip missing IDs gracefully on older versions)
    weight_tag_ids = []
    for name in ("Tweights", "Tvertexmap"):
        tid = getattr(c4d, name, None)
        if isinstance(tid, int) and tid:
            weight_tag_ids.append(tid)

    if not weight_tag_ids:
        return 0

    count = 0

    # Optionally clear existing tag selections
    if clear_existing:
        for obj in get_all_objects(doc):
            try:
                for tag in obj.GetTags() or []:
                    tag.DelBit(c4d.BIT_ACTIVE)
            except Exception:
                pass

    # Select all matching tags
    for obj in get_all_objects(doc):
        try:
            for tag in obj.GetTags() or []:
                try:
                    for tid in weight_tag_ids:
                        if tag.CheckType(tid):
                            tag.SetBit(c4d.BIT_ACTIVE)
                            count += 1
                            break
                except Exception:
                    pass
        except Exception:
            pass

    c4d.EventAdd()
    return count
