"""
Simple HTTP server for serving the frontend static files.
This serves the HTML/CSS/JS frontend for the document management system.

In production, this would be served by nginx or a CDN.
For development, we use Python's built-in HTTP server with CORS headers.
"""

import http.server
import socketserver
import os
import functools

PORT = 3000
DIRECTORY = os.path.join(os.path.dirname(__file__), "src")


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with CORS headers for frontend-backend communication."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()


if __name__ == "__main__":
    handler = functools.partial(CustomHandler)
    with socketserver.TCPServer(("0.0.0.0", PORT), handler) as httpd:
        print(f"Frontend server running at http://localhost:{PORT}")
        httpd.serve_forever()
