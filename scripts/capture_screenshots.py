"""PHANTOM — Automated Headless UI Screenshot Capture.

Serves frontend/dist locally and uses headless Chrome to capture real screenshots
of Dashboard, Network Explorer, Investigation Detail, and New Customer Onboarding.
"""

from __future__ import annotations

import functools
import http.server
import os
import socketserver
import subprocess
import threading
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "frontend" / "dist"
OUT_DIR = ROOT_DIR / "docs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CHROME_BIN = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    """Serve SPA fallback to index.html for React Router."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST_DIR), **kwargs)

    def do_GET(self):
        # If file does not exist, serve index.html
        path = self.translate_path(self.path)
        if not os.path.exists(path) and not path.endswith(".js") and not path.endswith(".css"):
            self.path = "/index.html"
        return super().do_GET()


def capture_all():
    port = 4173
    handler = SPAHandler
    server = socketserver.TCPServer(("127.0.0.1", port), handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"[Screenshots] Local SPA server started on http://127.0.0.1:{port}")
    time.sleep(1.0)

    pages = [
        ("dashboard.png", f"http://127.0.0.1:{port}/dashboard"),
        ("network_explorer.png", f"http://127.0.0.1:{port}/network"),
        ("investigation_detail.png", f"http://127.0.0.1:{port}/investigations/INV-2026-PHANTOM-001"),
        ("new_customer_onboarding.png", f"http://127.0.0.1:{port}/customers/new"),
    ]

    for fname, url in pages:
        out_path = OUT_DIR / fname
        cmd = [
            CHROME_BIN,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--window-size=1440,900",
            "--virtual-time-budget=4000",
            f"--screenshot={out_path}",
            url,
        ]
        print(f"[Screenshots] Capturing {fname} from {url}...")
        try:
            res = subprocess.run(cmd, timeout=20, capture_output=True)
            if out_path.exists():
                print(f"[Screenshots] Captured: {fname} ({out_path.stat().st_size:,} bytes)")
            else:
                print(f"[Screenshots] Failed to create {fname}: {res.stderr.decode('utf-8', errors='ignore')}")
        except Exception as e:
            print(f"[Screenshots] Error running Chrome: {e}")

    server.shutdown()
    print("[Screenshots] Server stopped. Capture phase complete.")


if __name__ == "__main__":
    capture_all()

