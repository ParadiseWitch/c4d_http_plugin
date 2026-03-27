import importlib
import sys
import types
import unittest


class FakeDoc(dict):
    pass


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
        self.assertEqual(float(sys.maxint) / 100.0, self.doc["far"])
        self.assertEqual({"near": 0.0, "far": float(sys.maxint)}, result)


if __name__ == "__main__":
    unittest.main()
