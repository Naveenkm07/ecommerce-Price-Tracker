from http.server import HTTPServer
import os
from api.scrape import handler


def run(host: str = "127.0.0.1", port: int = 3000) -> None:
    httpd = HTTPServer((host, port), handler)
    print(f"Serving on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("Server stopped.")


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    try:
        port = int(os.getenv("PORT", "3000"))
    except ValueError:
        port = 3000
    run(host, port)
