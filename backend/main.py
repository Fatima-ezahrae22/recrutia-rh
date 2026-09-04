"""
Module : main.py
Rôle   : Application principale FastAPI — API REST complète de RecrutIA RH.
         Architecture modularisée utilisant les APIRouter (auth, offres, candidatures, dashboard).
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.database import init_db
from backend.models import Offre, User
from backend.auth import hash_password

from backend.routers import auth, offres, candidatures, dashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RecrutIA.Backend")

# ✅ Initialisation DB (crée les tables si inexistantes)
init_db()


from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

# ─── GESTIONNAIRE WEBSOCKET (NOTIFICATION TEMPS RÉEL) ─────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"[WebSocket] Nouveau client connecté ({len(self.active_connections)} actifs)")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"[WebSocket] Client déconnecté ({len(self.active_connections)} actifs)")

    async def broadcast(self, message: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"[WebSocket] Erreur d'envoi client: {e}")
                self.disconnect(connection)

ws_manager = ConnectionManager()


def _creer_offres_demo():
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        count = db.query(Offre).count()
        if count == 0:
            offres_demo = [
                Offre(titre="Développeur Full Stack React/Python", description="Conception et développement d'applications web modernes pour ArtiWeb Fès.", experience_min_annees=3, competences_obligatoires=["React", "Python", "FastAPI", "PostgreSQL"], competences_souhaitees=["Docker", "Git", "REST API"], formation_exigee="Bac+3 minimum", seuil_score_min=70.0, statut="ACTIF"),
                Offre(titre="Data Scientist / Intelligence Artificielle", description="Analyse de données massives et développement de modèles IA innovants.", experience_min_annees=2, competences_obligatoires=["Python", "TensorFlow", "NLP", "Scikit-Learn"], competences_souhaitees=["Power BI", "Spark", "MLflow"], formation_exigee="Bac+4 minimum", seuil_score_min=75.0, statut="ACTIF"),
                Offre(titre="Designer UI/UX", description="Création d'interfaces utilisateur premium et expériences utilisateur exceptionnelles.", experience_min_annees=1, competences_obligatoires=["Figma", "Adobe XD", "Prototypage", "CSS"], competences_souhaitees=["Motion Design", "Framer"], formation_exigee="Bac+2 minimum", seuil_score_min=65.0, statut="ACTIF"),
            ]
            for o in offres_demo:
                db.add(o)
            db.commit()
            logger.info("[Init] 3 offres de démonstration créées avec seuils configurés.")
    except Exception as e:
        logger.error(f"[Init] Erreur création offres démo : {e}")
        db.rollback()
    finally:
        db.close()

_creer_offres_demo()


# ─── Application FastAPI ───────────────────────────────────────────────────────
app = FastAPI(
    title="RecrutIA — Agent IA RH & Dashboard de Recrutement",
    description="API REST & Dashboard d'automatisation et de scoring intelligent du recrutement.",
    version="5.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Endpoint WebSocket pour notifications en direct
@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        await websocket.send_json({
            "event": "CONNEXION_ETABLIE",
            "message": "Connexion WebSocket active avec RecrutIA RH",
            "timestamp": os.getenv("CURRENT_TIME", "")
        })
        while True:
            data = await websocket.receive_text()
            # Echo / Keepalive heartbeats
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"[WebSocket] Exception : {e}")
        ws_manager.disconnect(websocket)

# ✅ Servir les fichiers CV uploadés (dossier uploads/)
os.makedirs("uploads/cv", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ─── Inclusions des Routers ───────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(offres.router)
app.include_router(candidatures.router)
app.include_router(dashboard.router)


# ─────────────────────────────────────────────────────────────
# PAGES WEB (HTML UI)
# ─────────────────────────────────────────────────────────────

@app.get("/reset", response_class=HTMLResponse, tags=["Dashboard Web UI"])
def reset_et_rediriger():
    """Efface le localStorage et redirige vers /rh."""
    return HTMLResponse("""
<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>RecrutIA — Réinitialisation...</title>
<style>body{font-family:Inter,sans-serif;background:#0F172A;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;flex-direction:column;gap:16px;}</style>
</head><body>
<div style="text-align:center;">
<div style="width:60px;height:60px;background:#059669;border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:28px;margin:0 auto 20px;">🔄</div>
<h2>Réinitialisation en cours...</h2>
<p style="color:#94A3B8;font-size:14px;">Effacement du cache et reconnexion automatique.</p>
</div>
<script>
  localStorage.clear(); sessionStorage.clear();
  document.cookie.split(";").forEach(function(c){document.cookie=c.replace(/^ +/,"").replace(/=.*/,"=;expires="+new Date().toUTCString()+";path=/");});
  setTimeout(function(){window.location.replace('/rh');},1000);
</script>
</body></html>""", headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"})


@app.get("/", response_class=HTMLResponse, tags=["Dashboard Web UI"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard Web UI"])
@app.get("/rh", response_class=HTMLResponse, tags=["Dashboard Web UI"])
def servir_dashboard_rh():
    """Sert l'interface RH (tableau de bord recruteur)."""
    no_cache = {"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0", "Pragma": "no-cache", "Expires": "0"}
    chemin = os.path.join("frontend", "rh", "index.html")
    if os.path.exists(chemin):
        return FileResponse(chemin, headers=no_cache)
    chemin_legacy = os.path.join("frontend", "index.html")
    if os.path.exists(chemin_legacy):
        return FileResponse(chemin_legacy, headers=no_cache)
    return HTMLResponse("<h1>RecrutIA RH — Interface non trouvée.</h1>")


@app.get("/rh/register", response_class=HTMLResponse, tags=["Dashboard Web UI"])
def servir_inscription_rh():
    """Sert la page d'inscription RH."""
    chemin = os.path.join("frontend", "rh", "register.html")
    headers = {"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}
    if os.path.exists(chemin):
        return FileResponse(chemin, headers=headers)
    return HTMLResponse("<h1>RecrutIA Inscription RH — Interface non trouvée.</h1>")


@app.get("/candidat", response_class=HTMLResponse, tags=["Dashboard Web UI"])
def servir_dashboard_candidat():
    """Sert l'interface publique candidat."""
    chemin = os.path.join("frontend", "candidat", "index.html")
    headers = {"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}
    if os.path.exists(chemin):
        return FileResponse(chemin, headers=headers)
    return HTMLResponse("<h1>RecrutIA Candidat — Interface non trouvée.</h1>")