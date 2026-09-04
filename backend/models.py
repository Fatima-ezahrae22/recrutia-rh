"""
Module : models.py
Rôle   : Modèles ORM SQLAlchemy pour la base de données SQLite/PostgreSQL.
         Tables : User, Offre, Candidat, Candidature, AuditLog.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
)
from sqlalchemy.orm import relationship

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="recruteur")   # recruteur, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Offre(Base):
    __tablename__ = "offres"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    experience_min_annees = Column(Integer, default=0)
    competences_obligatoires = Column(JSON, default=list)
    competences_souhaitees = Column(JSON, default=list)
    formation_exigee = Column(String(100), default="Master / Ingénieur")
    seuil_score_min = Column(Float, default=70.0)  # ✅ Seuil d'adéquation configurable par offre
    statut = Column(String(50), default="ACTIF")
    created_at = Column(DateTime, default=datetime.utcnow)

    candidatures = relationship("Candidature", back_populates="offre", cascade="all, delete-orphan")


class Candidat(Base):
    __tablename__ = "candidats"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(150), nullable=True)
    email = Column(String(150), nullable=True, index=True)
    telephone = Column(String(50), nullable=True)
    cv_fichier_nom = Column(String(255), nullable=False)
    cv_chemin_stocke = Column(String(500), nullable=True)   # ✅ Chemin physique du CV sauvegardé
    created_at = Column(DateTime, default=datetime.utcnow)

    candidatures = relationship("Candidature", back_populates="candidat", cascade="all, delete-orphan")


class Candidature(Base):
    __tablename__ = "candidatures"

    id = Column(Integer, primary_key=True, index=True)
    offre_id = Column(Integer, ForeignKey("offres.id", ondelete="CASCADE"), nullable=False, index=True)
    candidat_id = Column(Integer, ForeignKey("candidats.id", ondelete="CASCADE"), nullable=False, index=True)

    statut_ingestion = Column(String(50), default="EN_COURS")
    raw_ingestion_json = Column(JSON, nullable=True)

    score = Column(Float, default=0.0, index=True)
    statut_ia = Column(String(50), default="EN_COURS")
    justification_ia = Column(Text, nullable=True)
    details_scoring = Column(JSON, nullable=True)

    # ✅ Statut candidature visible par le candidat : EN_ATTENTE, ACCEPTE, REFUSE
    statut = Column(String(50), default="EN_ATTENTE")
    decision_rh = Column(String(50), default="EN_ATTENTE")
    note_rh = Column(Text, nullable=True)
    rh_utilisateur = Column(String(100), default="Equipe RH")

    # Planification de l'entretien
    date_entretien = Column(String(200), nullable=True)
    format_entretien_planifie = Column(String(50), nullable=True)
    lieu_entretien = Column(String(300), nullable=True)

    duree_traitement_sec = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    offre = relationship("Offre", back_populates="candidatures")
    candidat = relationship("Candidat", back_populates="candidatures")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False)
    entite_type = Column(String(50), nullable=False)
    entite_id = Column(Integer, nullable=True)
    utilisateur = Column(String(100), default="Systeme / RH")
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
