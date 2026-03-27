import importlib
import sys
import types
import unittest


class FakeDoc(dict):
    pass


class FakeObject(object):
    def __init__(self, type_id, check_type_matches=None):
        self._type_id = type_id
        self._check_type_matches = set(check_type_matches or [])

    def GetType(self):
        return self._type_id

    def CheckType(self, type_id):
        return type_id in self._check_type_matches


class ViewClippingTests(unittest.TestCase):
    def setUp(self):
        self.original_modules = {
            name: sys.modules.get(name) for name in ("c4d", "c4d.documents", "utils")
        }

        self.doc = FakeDoc()

        documents_module = types.ModuleType("c4d.documents")
        documents_module.GetActiveDocument = lambda: self.doc

        c4d_module = types.ModuleType("c4d")
        c4d_module.documents = documents_module
        c4d_module.BASEDRAW_SDISPLAY_GOURAUD = 1
        c4d_module.BASEDRAW_SDISPLAY_QUICK = 2
        c4d_module.BASEDRAW_SDISPLAY_FLAT = 3
        c4d_module.BASEDRAW_SDISPLAY_HIDDENLINE = 4
        c4d_module.BASEDRAW_SDISPLAY_NOSHADING = 5
        c4d_module.DOCUMENT_CLIPPING_PRESET = "preset"
        c4d_module.DOCUMENT_CLIPPING_PRESET_CUSTOM = "custom"
        c4d_module.DOCUMENT_CLIPPING_PRESET_NEAR = "near"
        c4d_module.DOCUMENT_CLIPPING_PRESET_FAR = "far"
        c4d_module.DRAWFLAGS_ONLY_ACTIVE_VIEW = 1
        c4d_module.DRAWFLAGS_FORCEFULLREDRAW = 2
        c4d_module.DrawViews = lambda flags: None
        c4d_module.EventAdd = lambda: None

        sys.modules["c4d"] = c4d_module
        sys.modules["c4d.documents"] = documents_module
        sys.modules.pop("utils", None)
        self.utils = importlib.import_module("utils")

    def tearDown(self):
        for name, module in self.original_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def test_set_active_view_clipping_uses_sys_maxint_and_new_field_names(self):
        if not hasattr(sys, "maxint"):
            sys.maxint = sys.maxsize

        result = self.utils.set_active_view_clipping()

        self.assertEqual("custom", self.doc["preset"])
        self.assertEqual(0.0, self.doc["near"])
        self.assertEqual(float(sys.maxint), self.doc["far"])
        self.assertEqual({"near": 0.0, "far": float(sys.maxint)}, result)

    def test_find_objects_by_types_uses_exact_get_type_match(self):
        fake_joint = FakeObject(type_id=101, check_type_matches=[101, 202])
        fake_polygon = FakeObject(type_id=202, check_type_matches=[202])

        self.utils.get_all_objects = lambda: [fake_joint, fake_polygon]

        matched = self.utils.find_objects_by_types((202,))

        self.assertEqual([fake_polygon], matched)


if __name__ == "__main__":
    unittest.main()
