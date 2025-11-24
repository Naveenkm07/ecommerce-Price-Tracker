from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import urllib.parse
import traceback

# Ensure the src/ folder (with the price_tracker package) is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from price_tracker.scraper import ScraperError, get_product_info  # type: ignore


class handler(BaseHTTPRequestHandler):  # Vercel Python runtime looks for `handler`
    HTML_PAGE = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Ecommerce Price Tracker – Local</title>
        <style>
          body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; color: #111; }
          .box { max-width: 720px; margin: 0 auto; }
          label { display:block; margin-top: 1rem; font-weight: 600; }
          input, select { width: 100%; padding: 0.6rem 0.7rem; font-size: 1rem; margin-top: 0.25rem; }
          button { margin-top: 1rem; padding: 0.6rem 0.9rem; font-size: 1rem; cursor: pointer; }
          pre { background: #f6f8fa; padding: 1rem; overflow: auto; }
          .muted { color: #666; }
        </style>
      </head>
      <body>
        <div class="box">
          <h1>Ecommerce Price Tracker</h1>
          <p class="muted">Local demo UI calling <code>/api/scrape</code>.</p>
          <label for="url">Product URL</label>
          <input id="url" type="url" placeholder="https://example.com/product" />
          <label for="site">Site</label>
          <select id="site">
            <option value="other">other (generic)</option>
            <option value="amazon">amazon</option>
            <option value="flipkart">flipkart</option>
          </select>
          <button id="go">Fetch price</button>
          <pre id="out" class="muted">Result will appear here.</pre>
        </div>
        <script>
          const $ = (s) => document.querySelector(s);
          $("#go").addEventListener("click", async () => {
            const url = $("#url").value.trim();
            const site = $("#site").value;
            const out = $("#out");
            if (!url) { out.textContent = "Please enter a product URL."; return; }
            out.textContent = "Loading...";
            try {
              const qp = new URLSearchParams({ url, site });
              const res = await fetch(`/api/scrape?${qp.toString()}`);
              const data = await res.json();
              out.textContent = JSON.stringify(data, null, 2);
            } catch (e) {
              out.textContent = "Request failed: " + e;
            }
          });
        </script>
      </body>
    </html>
    """

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status: int, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        try:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path in ("/", "/index.html"):
                self._send_html(200, self.HTML_PAGE)
                return
            if parsed.path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            if parsed.path.startswith("/api/scrape"):
                params = urllib.parse.parse_qs(parsed.query)
                url = params.get("url", [None])[0]
                site = params.get("site", ["other"])[0]
                if not url:
                    self._send_json(400, {"ok": False, "error": "Missing 'url' query parameter"})
                    return
                info = get_product_info(url, site)
                self._send_json(200, {"ok": True, "data": info})
                return
            self._send_json(404, {"ok": False, "error": "Not found"})
        except ScraperError as exc:
            self._send_json(502, {"ok": False, "error": str(exc)})
        except Exception as exc:  # noqa: F841
            if os.getenv("DEBUG"):
                self._send_json(500, {"ok": False, "error": "Internal error", "trace": traceback.format_exc()})
            else:
                self._send_json(500, {"ok": False, "error": "Internal error"})

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length > 0 else b""
            payload: dict
            try:
                payload = json.loads(raw.decode("utf-8")) if raw else {}
            except Exception:
                payload = {}

            url = payload.get("url")
            site = payload.get("site", "other")
            if not url:
                self._send_json(400, {"ok": False, "error": "Missing 'url' in JSON body"})
                return

            info = get_product_info(url, site)
            self._send_json(200, {"ok": True, "data": info})
        except ScraperError as exc:
            self._send_json(502, {"ok": False, "error": str(exc)})
        except Exception as exc:  # noqa: F841
            if os.getenv("DEBUG"):
                self._send_json(500, {"ok": False, "error": "Internal error", "trace": traceback.format_exc()})
            else:
                self._send_json(500, {"ok": False, "error": "Internal error"})
