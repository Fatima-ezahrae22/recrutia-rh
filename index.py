import sys
import os
import traceback

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from backend.main import app as fastapi_app
    import_err = None
except Exception as e:
    import_err = traceback.format_exc()

async def app(scope, receive, send):
    if import_err:
        if scope.get("type") == "http":
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [[b"content-type", b"text/plain; charset=utf-8"]]
            })
            await send({
                "type": "http.response.body",
                "body": f"VERCEL IMPORT ERROR:\n{import_err}".encode("utf-8")
            })
        return

    if scope.get("type") == "http":
        path = scope.get("path", "")
        if path.startswith("/api/index.py"):
            new_path = path[13:]
            if not new_path or new_path == "":
                new_path = "/"
            scope["path"] = new_path
            scope["raw_path"] = new_path.encode("ascii")
    try:
        await fastapi_app(scope, receive, send)
    except Exception as e:
        err = traceback.format_exc()
        if scope.get("type") == "http":
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [[b"content-type", b"text/plain; charset=utf-8"]]
            })
            await send({
                "type": "http.response.body",
                "body": f"VERCEL RUNTIME ERROR:\n{err}".encode("utf-8")
            })
