# -*- coding: utf-8 -*-
import os

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


def _iter_tags(doc=None):
    for obj in get_all_objects(doc):
        try:
            for tag in obj.GetTags() or []:
                yield tag
        except Exception:
            pass


def _iter_materials(doc=None):
    if doc is None:
        doc = documents.GetActiveDocument()
    if doc is None:
        return

    material = doc.GetFirstMaterial()
    while material:
        yield material
        material = material.GetNext()


def _iter_animatables(doc=None):
    if doc is None:
        doc = documents.GetActiveDocument()
    if doc is None:
        return

    yield doc

    for obj in get_all_objects(doc):
        yield obj

    for tag in _iter_tags(doc):
        yield tag

    for material in _iter_materials(doc):
        yield material


def _get_track_key_count(track):
    if track is None:
        return 0

    try:
        curve = track.GetCurve()
        if curve is not None:
            return int(curve.GetKeyCount())
    except Exception:
        pass

    return 0


def _has_keyframe_animation(doc=None):
    for node in _iter_animatables(doc):
        try:
            for track in node.GetCTracks() or []:
                if _get_track_key_count(track) > 1:
                    return True
        except Exception:
            pass
    return False


def _has_type_match(nodes, type_ids):
    valid_type_ids = [tid for tid in type_ids if isinstance(tid, int) and tid]
    if not valid_type_ids:
        return False

    for node in nodes:
        try:
            for tid in valid_type_ids:
                if node.CheckType(tid):
                    return True
        except Exception:
            pass
    return False


def _has_simulation_animation(doc=None):
    if doc is None:
        doc = documents.GetActiveDocument()
    if doc is None:
        return False

    object_type_names = (
        "Oparticle",
        "Oemitter",
        "Oattractor",
        "Odeflector",
        "Owind",
        "Oturbulence",
        "Ofriction",
        "Orotation",
        "Ogravity",
        "Ocollision",
        "Obodycapture",
        "Oconnector",
        "Opyrocluster",
        "Ometaball",
        "Ovolume",
    )
    tag_type_names = (
        "Tpointcache",
        "Tdynamicsbody",
        "Tcolliderbody",
        "Tsoftbody",
        "Tcloth",
        "Tclothbelt",
        "Tclothcollider",
        "Tcmotion",
        "Tca",
        "Tcacheproxytag",
        "Tfluid",
    )

    object_type_ids = [getattr(c4d, name, 0) for name in object_type_names]
    tag_type_ids = [getattr(c4d, name, 0) for name in tag_type_names]

    if _has_type_match(get_all_objects(doc), object_type_ids):
        return True

    if _has_type_match(_iter_tags(doc), tag_type_ids):
        return True

    try:
        particle_system = doc.GetParticleSystem()
        if particle_system:
            return True
    except Exception:
        pass

    return False


def has_animation(doc=None):
    if doc is None:
        doc = documents.GetActiveDocument()
    if doc is None:
        return False

    if _has_keyframe_animation(doc):
        return True

    # if _has_simulation_animation(doc):
    #     return True

    return False


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


def select_all_weight_tags(is_select=True):
    """Select all weight-related tags in the document.

    This targets C4D's Weight tag (joint weights) and Vertex Map tag, as
    both are commonly referred to as "权重标签" in workflows.

    Args:
        is_select: True selects all matching weight tags, False deselects
            matching weight tags.

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

    # Select or deselect matching weight tags without touching other tag types.
    for obj in get_all_objects(doc):
        try:
            for tag in obj.GetTags() or []:
                try:
                    for tid in weight_tag_ids:
                        if tag.CheckType(tid):
                            if is_select:
                                tag.SetBit(c4d.BIT_ACTIVE)
                            else:
                                tag.DelBit(c4d.BIT_ACTIVE)
                            count += 1
                            break
                except Exception:
                    pass
        except Exception:
            pass

    c4d.EventAdd()
    return count


def _iter_existing_layout_dirs():
    candidate_dirs = []

    try:
        candidate_dirs.append(c4d.storage.GeGetC4DPath(c4d.C4D_PATH_PREFS))
    except Exception:
        pass

    try:
        candidate_dirs.append(c4d.storage.GeGetStartupWritePath())
    except Exception:
        pass

    try:
        candidate_dirs.append(c4d.storage.GeGetStartupPath())
    except Exception:
        pass

    subdirs = (
        "",
        "layout",
        "layouts",
        os.path.join("library", "layout"),
        os.path.join("library", "layouts"),
        os.path.join("prefs", "layout"),
        os.path.join("prefs", "layouts"),
    )

    seen = set()
    for base_dir in candidate_dirs:
        if not base_dir:
            continue
        for subdir in subdirs:
            path = os.path.normpath(os.path.join(base_dir, subdir))
            key = path.lower()
            if key in seen:
                continue
            seen.add(key)
            if os.path.isdir(path):
                yield path


def _find_layout_file(layout_name):
    if not layout_name:
        return None, []

    layout_name = layout_name.strip()
    if not layout_name:
        return None, []

    searched_dirs = []
    candidate_names = [layout_name]
    if not layout_name.lower().endswith(".l4d"):
        candidate_names.append(layout_name + ".l4d")

    if os.path.isfile(layout_name):
        return os.path.normpath(layout_name), searched_dirs

    lower_names = tuple(name.lower() for name in candidate_names)
    for layout_dir in _iter_existing_layout_dirs():
        searched_dirs.append(layout_dir)
        try:
            for root, _, files in os.walk(layout_dir):
                for filename in files:
                    if filename.lower() in lower_names:
                        return os.path.normpath(
                            os.path.join(root, filename)
                        ), searched_dirs
        except Exception:
            pass

    return None, searched_dirs


def set_layout(layout_name):
    layout_path, searched_dirs = _find_layout_file(layout_name)
    if not layout_path:
        return {
            "ok": False,
            "error": "layout-not-found",
            "layoutName": layout_name,
            "searchedDirs": searched_dirs,
        }

    try:
        documents.LoadFile(layout_path)
    except Exception as exc:
        return {
            "ok": False,
            "error": "load-layout-exception",
            "layoutName": layout_name,
            "layoutPath": layout_path,
            "message": str(exc),
        }

    c4d.EventAdd()
    return {"ok": True, "layoutName": layout_name, "layoutPath": layout_path}
