# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane. All rights reserved.
#
# Stdlib-only static server for the prebuilt frontend (dist/).
# No pip packages, no internet, no artifactory — runs on any Python 3.7+.
#
#   python serve.py            # serves ./dist on http://127.0.0.1:8080
#   python serve.py 9000       # custom port
#
# Falls back to index.html for unknown paths so client-side routes survive a refresh.

import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")


class SPAHandler(SimpleHTTPRequestHandler):
    # Ensure ES modules are served with a JS MIME type on every Python version.
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".css": "text/css",
        ".svg": "image/svg+xml",
        ".json": "application/json",
        ".wasm": "application/wasm",
    }

    def send_head(self):
        path = self.translate_path(self.path)
        # If the requested file does not exist and it is not an asset request,
        # serve index.html so the SPA router can handle the route.
        if not os.path.exists(path) and not self.path.startswith("/assets/"):
            self.path = "/index.html"
        return super().send_head()


if __name__ == "__main__":
    if not os.path.isdir(ROOT):
        sys.exit(f"dist/ not found at {ROOT} — run the build first.")
    handler = partial(SPAHandler, directory=ROOT)
    with ThreadingHTTPServer(("127.0.0.1", PORT), handler) as httpd:
        print(f"Serving {ROOT} at http://127.0.0.1:{PORT}  (Ctrl+C to stop)")
        httpd.serve_forever()
