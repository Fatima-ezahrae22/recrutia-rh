import sys
import os
import traceback

# Ajouter le répertoire racine du projet au sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from backend.main import app
except Exception as e:
    # Si l'import échoue, créer une app minimale qui AFFICHE l'erreur exacte
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    app = FastAPI()
    error_detail = traceback.format_exc()

    @app.get("/{path:path}")
    async def show_error(path: str = ""):
        return HTMLResponse(f"""
        <html><head><title>RecrutIA - Diagnostic</title></head>
        <body style="font-family:monospace;background:#1e1e1e;color:#f8f8f2;padding:40px;">
        <h2 style="color:#ff6b6b;">Erreur d'import detectee sur Vercel</h2>
        <pre style="background:#2d2d2d;padding:20px;border-radius:8px;overflow-x:auto;color:#a9dc76;">{error_detail}</pre>
        <p style="color:#78dce8;">ROOT_DIR: {root_dir}</p>
        <p style="color:#78dce8;">SYS.PATH: {sys.path[:5]}</p>
        <p style="color:#78dce8;">FILES in root: {os.listdir(root_dir)[:20]}</p>
        </body></html>
        """)
