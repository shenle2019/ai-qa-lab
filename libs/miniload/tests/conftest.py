import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/slow":
            time.sleep(0.15)
        if self.path == "/error":
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"error")
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
