# -*- coding: utf-8 -*-
"""Cinema 4D 场景查询与视图控制工具函数模块。"""

import os
import sys

import c4d
from c4d import documents


DISPLAY_MODE_MAP = {
    "光影着色": c4d.BASEDRAW_SDISPLAY_GOURAUD,
    "快速着色": c4d.BASEDRAW_SDISPLAY_QUICK,
    "常量着色": c4d.BASEDRAW_SDISPLAY_FLAT,
    "隐藏线条": c4d.BASEDRAW_SDISPLAY_HIDDENLINE,
    "线框": c4d.BASEDRAW_SDISPLAY_NOSHADING,
}


def _as_bool(val, default=True):
    """将常见的字符串或布尔值转换为布尔类型。"""
    if isinstance(val, bool):
        return val
    s = str(val).lower().strip().lower()
    if s in ("1", "true", "yes", "on"):
        return True
    if s in ("0", "false", "no", "off"):
        return False
    return default


def _as_float(val, default):
    """将输入值转换为浮点数，失败时返回默认值。"""
    try:
        return float(val)
    except (TypeError, ValueError):
        return float(default)


def iter_objects(root):
    """从根对象开始深度优先遍历所有层级对象。"""
    result = []
    op = root
    while op:
        result.append(op)
        child = op.GetDown()
        if child:
            result.extend(iter_objects(child))
        op = op.GetNext()
    return result


def get_all_objects():
    """返回指定文档或当前活动文档中的全部对象列表。"""
    doc = documents.GetActiveDocument()
    res = []
    roots = doc.GetObjects()

    for r in roots:
        for obj in iter_objects(r):
            res.append(obj)
    return res


def find_objects_by_types(type_ids):
    """按类型 ID 列表筛选并返回匹配的对象。"""
    doc = documents.GetActiveDocument()
    objs = get_all_objects()
    matched = []
    for obj in objs:
        try:
            obj_type = obj.GetType()
            for tid in type_ids:
                if tid and obj_type == tid:
                    matched.append(obj)
                    break
        except Exception:
            pass
    return matched


def get_all_joints():
    """返回当前文档中的所有关节或骨骼对象。"""
    return find_objects_by_types((getattr(c4d, "Ojoint", 0), getattr(c4d, "Obone", 0)))


def get_all_polygons():
    """返回当前文档中的所有多边形对象。"""
    return find_objects_by_types((getattr(c4d, "Opolygon", 0),))


def get_all_cameras():
    """返回当前文档中的所有摄像机对象。"""
    return find_objects_by_types((getattr(c4d, "Ocamera", 0),))


def _iter_tags():
    """遍历文档中所有对象挂载的标签。"""
    tags = []
    for obj in get_all_objects():
        try:
            tags.extend(obj.GetTags() or [])
        except Exception:
            pass
    return tags


def _iter_materials():
    """遍历指定文档或当前活动文档中的全部材质。"""
    doc = documents.GetActiveDocument()
    materials = []
    material = doc.GetFirstMaterial()
    while material:
        materials.append(material)
        material = material.GetNext()
    return materials


def _iter_animatables():
    """遍历可能包含动画轨道的文档节点集合。"""
    doc = documents.GetActiveDocument()
    nodes = [doc]

    nodes.extend(get_all_objects())
    nodes.extend(_iter_tags())
    nodes.extend(_iter_materials())

    return nodes


def _get_track_key_count(track):
    """获取单条动画轨道上的关键帧数量。"""
    if track is None:
        return 0

    try:
        curve = track.GetCurve()
        if curve is not None:
            return int(curve.GetKeyCount())
    except Exception:
        pass

    return 0


def _has_keyframe_animation():
    """检查文档是否包含关键帧动画。"""
    for node in _iter_animatables():
        try:
            for track in node.GetCTracks() or []:
                if _get_track_key_count(track) > 1:
                    return True
        except Exception:
            pass
    return False


def _has_type_match(nodes, type_ids):
    """检查节点集合中是否存在任意匹配指定类型 ID 的节点。"""
    valid_type_ids = [tid for tid in type_ids if isinstance(tid, int) and tid]
    if not valid_type_ids:
        return False

    for node in nodes:
        try:
            node_type = node.GetType()
            for tid in valid_type_ids:
                if node_type == tid:
                    return True
        except Exception:
            pass
    return False


def _has_simulation_animation():
    """检查文档是否包含模拟类动画对象、标签或粒子系统。"""
    doc = documents.GetActiveDocument()

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

    if _has_type_match(get_all_objects(), object_type_ids):
        return True

    if _has_type_match(_iter_tags(), tag_type_ids):
        return True

    try:
        particle_system = doc.GetParticleSystem()
        if particle_system:
            return True
    except Exception:
        pass

    return False


def has_animation():
    """检查当前文档是否存在可识别的动画内容。"""
    if _has_keyframe_animation():
        return True

    return False


def set_joint_visibility(value):
    """批量设置所有关节对象在编辑器中的可见性。"""
    doc = documents.GetActiveDocument()
    for obj in get_all_joints():
        try:
            obj[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = value
        except Exception:
            pass
    c4d.EventAdd()


def set_polygon_visibility(value):
    """批量设置所有多边形对象在编辑器中的可见性。"""
    doc = documents.GetActiveDocument()
    for obj in get_all_polygons():
        try:
            obj[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = value
        except Exception:
            pass
    c4d.EventAdd()


def enabel_joint_display_filter(value):
    """设置当前活动视图中的关节显示过滤器状态。"""
    doc = documents.GetActiveDocument()
    bd = doc.GetActiveBaseDraw()
    # 控制关节显示过滤器的开关状态。
    bd[c4d.BASEDRAW_DISPLAYFILTER_JOINT] = value
    c4d.EventAdd()


def enabel_polygon_display_filter(value):
    """设置当前活动视图中的多边形相关显示过滤器状态。"""
    doc = documents.GetActiveDocument()
    bd = doc.GetActiveBaseDraw()
    # 同步控制多边形及相关对象在视图中的显示状态。
    bd[c4d.BASEDRAW_DISPLAYFILTER_POLYGON] = value
    bd[c4d.BASEDRAW_DISPLAYFILTER_SPLINE] = value
    bd[c4d.BASEDRAW_DISPLAYFILTER_GENERATOR] = value
    bd[c4d.DISPLAYFILTER_HYPERNURBS] = value
    bd[c4d.DISPLAYFILTER_MULTIAXIS] = value

    c4d.EventAdd()


def set_active_view_display_mode(display_mode_name):
    """设置当前活动视图的显示模式。"""
    doc = documents.GetActiveDocument()
    if doc is None:
        raise RuntimeError("当前没有激活的文档")

    base_draw = doc.GetActiveBaseDraw()
    if base_draw is None:
        raise RuntimeError("当前没有可用的活动视图")

    display_mode_name = str(display_mode_name).strip()
    mode = DISPLAY_MODE_MAP.get(display_mode_name)
    if mode is None:
        raise ValueError(display_mode_name)

    base_draw[c4d.BASEDRAW_DATA_SDISPLAYACTIVE] = mode
    try:
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_FORCEFULLREDRAW)
    except Exception:
        pass

    c4d.EventAdd()
    return mode


def set_active_view_clipping(near=0, far=sys.maxint):
    """设置当前文档工程设置中的视图近裁剪与远裁剪范围，单位为厘米。"""
    doc = documents.GetActiveDocument()
    if doc is None:
        raise RuntimeError("当前没有激活的文档")

    near = _as_float(near, 0)
    far = _as_float(far, sys.maxint)

    if near < 0:
        raise ValueError("nearCm 不能小于 0")
    if far < near:
        raise ValueError("farCm 不能小于 nearCm")

    doc[c4d.DOCUMENT_CLIPPING_PRESET] = c4d.DOCUMENT_CLIPPING_PRESET_CUSTOM
    doc[c4d.DOCUMENT_CLIPPING_PRESET_NEAR] = near
    doc[c4d.DOCUMENT_CLIPPING_PRESET_FAR] = far

    try:
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_FORCEFULLREDRAW)
    except Exception:
        pass

    c4d.EventAdd()
    return {"near": near, "far": far}


def center_model_in_active_view():
    """若场景存在摄像机则切入摄像机视角，否则对几何体执行居中显示。"""
    doc = documents.GetActiveDocument()

    base_draw = doc.GetActiveBaseDraw()
    if base_draw is None:
        raise RuntimeError("当前没有可用的活动视图")

    cameras = get_all_cameras()
    if cameras:
        camera = cameras[0]
        base_draw.SetSceneCamera(camera)
        try:
            c4d.DrawViews(
                c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_FORCEFULLREDRAW
            )
        except Exception:
            pass
        c4d.EventAdd()
        return {"mode": "camera", "cameraName": camera.GetName()}

    base_draw.SetSceneCamera(None)
    c4d.CallCommand(12148)  # Frame Geometry
    try:
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_FORCEFULLREDRAW)
    except Exception:
        pass
    c4d.EventAdd()
    return {"mode": "geometry"}


def select_all_weight_tags(is_select=True):
    """批量选中或取消选中文档中的权重相关标签，并返回处理数量。"""
    doc = documents.GetActiveDocument()
    if doc is None:
        return 0

    # 收集可能存在的权重标签类型，兼容旧版本中缺失常量的情况。
    weight_tag_ids = []
    for name in ("Tweights", "Tvertexmap"):
        tid = getattr(c4d, name, None)
        if isinstance(tid, int) and tid:
            weight_tag_ids.append(tid)

    if not weight_tag_ids:
        return 0

    count = 0

    # 仅处理匹配的权重标签，不影响其他类型的标签。
    for obj in get_all_objects():
        try:
            for tag in obj.GetTags() or []:
                try:
                    tag_type = tag.GetType()
                    for tid in weight_tag_ids:
                        if tag_type == tid:
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
    """遍历当前环境中可能存在布局文件的目录。"""
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
    result = []
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
                result.append(path)
    return result


def _find_layout_file(layout_name):
    """根据布局名称或路径查找实际可用的布局文件。"""
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
    """加载指定的布局文件并刷新 Cinema 4D 界面。"""
    layout_path, searched_dirs = _find_layout_file(layout_name)
    if not layout_path:
        raise IOError("layout-not-found: {}".format(",".join(searched_dirs)))

    documents.LoadFile(layout_path)

    c4d.EventAdd()
    return layout_path
