"""
Simple HTTP server for the OsifShop barcode scanner Mini App.
Serves static files from /app/webapp/ on port 8080.
"""
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = int(os.getenv("WEBAPP_PORT", "8080"))
DIRECTORY = os.path.join(os.path.dirname(__file__), "webapp")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # CORS headers for Telegram
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Serving Mini App on port {PORT}")
    server.serve_forever()
