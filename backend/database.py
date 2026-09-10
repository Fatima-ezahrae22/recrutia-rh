"""
Module : database.py
Rôle   : Configuration du moteur de base de données SQLAlchemy.
         Supporte PostgreSQL (via DATABASE_URL) avec fallback automatique sur SQLite local.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

def _get_database_url():
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        if env_url.startswith("postgres://"):
            env_url = env_url.replace("postgres://", "postgresql://", 1)
        return env_url
    if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return "sqlite:////tmp/agent_rh.db"
    try:
        test_path = "./.write_test"
        with open(test_path, "w") as f:
            f.write("ok")
        os.remove(test_path)
        return "sqlite:///./agent_rh.db"
    except Exception:
        return "sqlite:////tmp/agent_rh.db"

DATABASE_URL = _get_database_url()

# Configuration du moteur selon le SGBD
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # Requis pour SQLite avec FastAPI multithread
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dépendance FastAPI pour obtenir une session DB par requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from sqlalchemy import text

def init_db():
    """Initialise les tables de la base de données et applique les migrations de colonnes."""
    try:
        logger.info(f"[Database] Initialisation des tables SQLAlchemy sur : {DATABASE_URL}")
        Base.metadata.create_all(bind=engine)
        
        # ✅ Migration automatique : Ajout de la colonne cv_base64 si absente (PostgreSQL & SQLite)
        with engine.connect() as conn:
            try:
                if DATABASE_URL.startswith("sqlite"):
                    conn.execute(text("ALTER TABLE candidats ADD COLUMN cv_base64 TEXT;"))
                else:
                    conn.execute(text("ALTER TABLE candidats ADD COLUMN IF NOT EXISTS cv_base64 TEXT;"))
                conn.commit()
                logger.info("[Database] Migration cv_base64 appliquée avec succès.")
            except Exception as e_col:
                logger.info(f"[Database] Info colonne cv_base64 (déjà présente ou ignorée) : {e_col}")
    except Exception as e:
        logger.error(f"[Database] Erreur lors de l'initialisation des tables : {e}")
