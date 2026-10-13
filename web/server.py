"""Serve the page and answer /api/ask with the bot. Local use: python web/server.py"""
import json
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bot.answer import ask  # noqa: E402


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "web"), **kwargs)

    def do_POST(self):
        if self.path != "/api/ask":
            self.send_error(404)
            return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        out = ask(body["question"])
        payload = json.dumps({"answer": out["answer"], "sources": out["sources"]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    print("http://localhost:4173")
    HTTPServer(("localhost", 4173), Handler).serve_forever()
