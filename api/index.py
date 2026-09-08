import sys
import os

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.main import app as fastapi_app

async def app(scope, receive, send):
    if scope.get("type") == "http":
        path = scope.get("path", "")
        if path.startswith("/api/index.py"):
            new_path = path[13:]
            if not new_path or new_path == "":
                new_path = "/"
            scope["path"] = new_path
    await fastapi_app(scope, receive, send)
