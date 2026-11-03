import os
import sys

# Ensure root directory is on python path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app


class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # 1. Check user-facing URL headers passed by reverse proxy
        for h in ["HTTP_X_FORWARDED_URI", "HTTP_X_ORIGINAL_URI", "HTTP_X_REWRITE_URL"]:
            val = environ.get(h)
            if val:
                clean = val.lstrip("/")
                if not any(clean.startswith(p) for p in ["api/index.py", "api/index"]):
                    target = val.split("?")[0]
                    environ["PATH_INFO"] = target if target.startswith("/") else ("/" + target)
                    return self.wsgi_app(environ, start_response)

        # 2. Inspect and normalize PATH_INFO
        path = environ.get("PATH_INFO", "") or "/"
        if not path.startswith("/"):
            path = "/" + path

        clean = path.lstrip("/")
        for p in ["api/index.py", "api/index"]:
            if clean == p or clean == p + "/":
                path = "/"
                break
            elif clean.startswith(p + "/"):
                rem = clean[len(p):]
                path = rem if rem.startswith("/") else ("/" + rem)
                break

        environ["PATH_INFO"] = path
        return self.wsgi_app(environ, start_response)


# Apply WSGI path normalization
app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
app.debug = False

# Top-level WSGI entrypoints detected by Vercel
handler = app
application = app

