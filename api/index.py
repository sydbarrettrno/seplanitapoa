from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.final_entry import dashboard, health, query_from_params


def _flatten(query_string: str) -> dict[str, str]:
    parsed = parse_qs(query_string, keep_blank_values=False)
    return {key: values[-1] for key, values in parsed.items() if values}


class handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            params = _flatten(parsed.query)
            action = params.pop("action", "dashboard")
            if action == "health":
                self._json(200, health())
                return
            if action != "dashboard":
                self._json(400, {"ok": False, "error": "Ação inválida."})
                return
            self._json(200, dashboard(query_from_params(params)))
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)})

    def log_message(self, format, *args):
        return
