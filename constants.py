# -*- coding: utf-8 -*-
import os

# Replace with official IDs from Plug-in Cafe for production
COMMAND_PLUGIN_ID = 1070002  # Command plugin: menu toggle
MESSAGE_PLUGIN_ID = 1070003  # Message plugin: processes SpecialEvent tasks


def env_host_port():
    host = os.environ.get('C4D_HTTP_HOST', '127.0.0.1')
    port_str = os.environ.get('C4D_HTTP_PORT', '8090')
    try:
        port = int(port_str)
    except Exception:
        port = 8090
    return host, port

