import sys
import os

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.main import app as fastapi_app

async def app(scope, receive, send):
    if scope.get("type") == "http":
        path = scope.get("path", "")
        # Vercel réécrit vers /api/index.py/... ou /api/index.py
        if path.startswith("/api/index.py"):
            path = path[len("/api/index.py"):]
        if not path or path == "":
            path = "/"
        # Normaliser les slashes
        while "//" in path:
            path = path.replace("//", "/")
        scope["path"] = path
        scope["raw_path"] = path.encode("ascii")
    await fastapi_app(scope, receive, send)
