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

# URL par défaut : PostgreSQL si configuré, sinon SQLite local 'agent_rh.db'
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./agent_rh.db"
)

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


def init_db():
    """Initialise les tables de la base de données."""
    logger.info(f"[Database] Initialisation des tables SQLAlchemy sur : {DATABASE_URL}")
    Base.metadata.create_all(bind=engine)
