# -*- coding: utf-8 -*-
"""
Cinema 4D plugin entry. Actual implementation split into modules:
- constants.py: IDs, env config
- operations.py: C4D scene operations
- tasks.py: task queue and main-thread processing
- server.py: HTTP server and routes
- plugin.py: plugin classes and registration
"""

import os
import sys

# Ensure this plugin folder is importable for sibling modules in C4D R19
try:
    _BASE_DIR = os.path.dirname(__file__)
except Exception:
    _BASE_DIR = os.getcwd()
if _BASE_DIR and _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

import plugin as http_plugin


if __name__ == "__main__":
    http_plugin.register()
