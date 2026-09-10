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
                Offre(titre="Ingénieur DevOps & Cloud AWS/Docker", description="Gestion de l'infrastructure Cloud, automatisation des pipelines CI/CD, conteneurisation des applications.", experience_min_annees=3, competences_obligatoires=["Docker", "Linux", "AWS", "Git", "CI/CD"], competences_souhaitees=["Kubernetes", "Terraform"], formation_exigee="Bac+3 minimum", seuil_score_min=70.0, statut="ACTIF"),
                Offre(titre="Ingénieur Data / IA & Machine Learning", description="Conception de pipelines d'ingestion de données, prétraitement, entraînement et déploiement de modèles d'apprentissage.", experience_min_annees=2, competences_obligatoires=["Python", "Scikit-Learn", "Pandas", "NLP", "SQL"], competences_souhaitees=["TensorFlow", "PyTorch", "Spark"], formation_exigee="Bac+4 minimum", seuil_score_min=70.0, statut="ACTIF"),
                Offre(titre="Designer UI/UX & Product Designer", description="Création de maquettes haute fidélité, de design systems et de prototypes interactifs. Réalisation de tests utilisateur.", experience_min_annees=1, competences_obligatoires=["Figma", "Adobe XD", "Prototypage", "Design System", "CSS"], competences_souhaitees=["Framer", "Motion Design"], formation_exigee="Bac+2 minimum", seuil_score_min=70.0, statut="ACTIF"),
                Offre(titre="Développeur Full Stack React & Node.js", description="Rejoignez notre équipe Web pour créer des interfaces utilisateurs modernes, réactives et fluides en React / TypeScript.", experience_min_annees=2, competences_obligatoires=["React", "JavaScript", "TypeScript", "Node.js", "HTML/CSS"], competences_souhaitees=["Next.js", "TailwindCSS"], formation_exigee="Bac+3 minimum", seuil_score_min=70.0, statut="ACTIF"),
                Offre(titre="Développeur Senior Python / FastAPI & IA", description="Nous recherchons un développeur Backend chevronné pour concevoir des microservices performants, intégrer des modèles d'IA et créer des APIs REST.", experience_min_annees=3, competences_obligatoires=["Python", "FastAPI", "PostgreSQL", "SQLAlchemy", "Git"], competences_souhaitees=["Docker", "Redis", "Celery"], formation_exigee="Bac+3 minimum", seuil_score_min=70.0, statut="ACTIF"),
            ]
            for o in offres_demo:
                db.add(o)
            db.commit()
            logger.info("[Init] 5 offres de démonstration créées avec succès.")
    except Exception as e:
        logger.error(f"[Init] Erreur création offres démo : {e}")
        db.rollback()
    finally:
        db.close()

def _creer_utilisateurs_demo():
    from backend.database import SessionLocal
    from backend.models import User
    from backend.auth import hash_password
    db = SessionLocal()
    try:
        # Supprimer les comptes démo superflus pour conserver uniquement 'recruteur'
        db.query(User).filter(User.username != "recruteur").delete(synchronize_session=False)
        db.commit()

        # S'assurer que le compte unique RH 'recruteur' existe avec le mot de passe 'recruteur123'
        recruteur_user = db.query(User).filter(User.username == "recruteur").first()
        if not recruteur_user:
            recruteur_user = User(username="recruteur", hashed_password=hash_password("recruteur123"), role="recruteur", is_active=True)
            db.add(recruteur_user)
            db.commit()
            logger.info("[Init] Unique compte RH 'recruteur' créé avec succès.")
        else:
            logger.info("[Init] Compte unique RH 'recruteur' actif.")
    except Exception as e:
        logger.error(f"[Init] Erreur initialisation compte RH : {e}")
        db.rollback()
    finally:
        db.close()

def _creer_candidatures_demo():
    from backend.database import SessionLocal
    from backend.models import Candidat, Candidature, Offre
    db = SessionLocal()
    try:
        if db.query(Candidature).count() == 0:
            offres = db.query(Offre).all()
            if not offres:
                return

            offre_python = next((o for o in offres if "Python" in o.titre), offres[0])
            offre_data = next((o for o in offres if "Data" in o.titre or "IA" in o.titre), offres[0])

            candidats_demo = [
                {"nom": "Fatima Ezahrae Mekki", "email": "fatimaezaharemkki@gmail.com", "tel": "+212 6 61 22 33 44", "exp": 3, "comp": ["Python", "FastAPI", "React", "PostgreSQL"]},
                {"nom": "adil mekki", "email": "adil.mekki@gmail.com", "tel": "+212 6 62 33 44 55", "exp": 4, "comp": ["Python", "Scikit-Learn", "Pandas", "NLP"]},
                {"nom": "HANAE bouaasoul", "email": "hanae.bouaasoul@gmail.com", "tel": "+212 6 63 44 55 66", "exp": 3, "comp": ["Python", "Machine Learning", "Pandas", "SQL"]},
                {"nom": "Douae mekki", "email": "douae.mekki@gmail.com", "tel": "+212 6 64 55 66 77", "exp": 2, "comp": ["Python", "Data Science", "SQL", "Pandas"]}
            ]

            for c_data in candidats_demo:
                candidat = db.query(Candidat).filter(Candidat.email == c_data["email"]).first()
                if not candidat:
                    candidat = Candidat(
                        nom=c_data["nom"],
                        email=c_data["email"],
                        telephone=c_data["tel"],
                        annees_experience=c_data["exp"],
                        competences_json=c_data["comp"],
                        diplome="Master / Ingénieur"
                    )
                    db.add(candidat)
                    db.flush()

                # Candidature 1 sur Data / IA
                cand1 = Candidature(
                    candidat_id=candidat.id,
                    offre_id=offre_data.id,
                    score=81.2,
                    statut="EN_ATTENTE",
                    details_scoring={
                        "score_global": 81.2,
                        "hard_filter_pass": True,
                        "hard_filter_reasons": ["Expérience valide", "Formation diplômante conforme"],
                        "similarite_semantique": 82.0,
                        "justification_llm": "Profil très pertinent ! Vos compétences clés correspondent aux besoins prioritaires de l'offre.",
                        "atouts_majeurs": ["Python", "Scikit-Learn", "NLP", "SQL"],
                        "lacunes": []
                    }
                )
                db.add(cand1)

                # Si Fatima, ajouter aussi la 2eme candidature Senior Python (score 85%)
                if c_data["email"] == "fatimaezaharemkki@gmail.com":
                    cand2 = Candidature(
                        candidat_id=candidat.id,
                        offre_id=offre_python.id,
                        score=85.0,
                        statut="EN_ATTENTE",
                        details_scoring={
                            "score_global": 85.0,
                            "hard_filter_pass": True,
                            "hard_filter_reasons": ["3 ans d'expérience validés"],
                            "similarite_semantique": 86.0,
                            "justification_llm": "Excellente adéquation technique sur Python, FastAPI et architectures Web.",
                            "atouts_majeurs": ["Python", "FastAPI", "React", "PostgreSQL"],
                            "lacunes": []
                        }
                    )
                    db.add(cand2)

            db.commit()
            logger.info("[Init] Candidatures de démonstration créées avec succès.")
    except Exception as e:
        logger.error(f"[Init] Erreur création candidatures démo : {e}")
        db.rollback()
    finally:
        db.close()


# ✅ Initialisation DB & Données Démo (crée les tables, offres et candidatures démo)
try:
    init_db()
except Exception as e:
    logger.error(f"[Main] Erreur init_db : {e}")

try:
    _creer_offres_demo()
except Exception as e:
    logger.error(f"[Main] Erreur _creer_offres_demo : {e}")

try:
    _creer_utilisateurs_demo()
except Exception as e:
    logger.error(f"[Main] Erreur _creer_utilisateurs_demo : {e}")

try:
    _creer_candidatures_demo()
except Exception as e:
    logger.error(f"[Main] Erreur _creer_candidatures_demo : {e}")


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

def _setup_uploads_mount():
    try:
        os.makedirs("uploads/cv", exist_ok=True)
        app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    except Exception:
        try:
            tmp_cv = os.path.join("/tmp", "uploads", "cv")
            os.makedirs(tmp_cv, exist_ok=True)
            app.mount("/uploads", StaticFiles(directory=os.path.join("/tmp", "uploads")), name="uploads")
        except Exception as e:
            logger.warning(f"[Init] Montage static uploads non disponible : {e}")

_setup_uploads_mount()


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


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _lire_html(relative_path: str) -> str:
    try:
        chemin = os.path.join(BASE_DIR, relative_path)
        if os.path.exists(chemin):
            with open(chemin, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        logger.error(f"[HTML] Erreur lecture {relative_path} : {e}")
    return f"<h1>Interface RecrutIA RH — ({relative_path} non disponible)</h1>"


@app.get("/", response_class=HTMLResponse, tags=["Dashboard Web UI"])
@app.get("/candidat", response_class=HTMLResponse, tags=["Dashboard Web UI"])
def servir_dashboard_candidat():
    """Sert l'interface publique candidat (Page d'accueil principale)."""
    headers = {"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}
    html = _lire_html("frontend/candidat/index.html")
    return HTMLResponse(content=html, headers=headers)


@app.get("/rh/register", response_class=HTMLResponse, tags=["Dashboard Web UI"])
def servir_inscription_rh():
    """Sert la page d'inscription RH."""
    no_cache = {"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}
    html = _lire_html("frontend/rh/register.html")
    return HTMLResponse(content=html, headers=no_cache)


@app.get("/rh", response_class=HTMLResponse, tags=["Dashboard Web UI"])
@app.get("/admin", response_class=HTMLResponse, tags=["Dashboard Web UI"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard Web UI"])
def servir_dashboard_rh():
    """Sert l'interface RH (tableau de bord recruteur protégé)."""
    no_cache = {"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0", "Pragma": "no-cache", "Expires": "0"}
    html = _lire_html("frontend/rh/index.html")
    return HTMLResponse(content=html, headers=no_cache)