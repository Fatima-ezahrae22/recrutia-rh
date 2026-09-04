"""
Module : schemas.py
Rôle   : Schémas de validation Pydantic V2 pour l'API REST FastAPI.
"""

from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normaliser_liste_competences(v):
    """
    Tolère les anciennes données stockées comme chaîne "A,B,C" et les convertit en liste.
    """
    if v is None:
        return []
    if isinstance(v, str):
        return [s.strip() for s in v.split(",") if s.strip()]
    return v


# ── SCHÉMAS OFFRE ──

class OffreCreate(BaseModel):
    titre: str = Field(..., json_schema_extra={"example": "Développeur Senior Backend Python / Django"})
    description: str = Field(..., json_schema_extra={"example": "Conception et développement d'API REST performantes..."})
    experience_min_annees: int = Field(0, json_schema_extra={"example": 3})
    competences_obligatoires: List[str] = Field(default_factory=list, json_schema_extra={"example": ["Python", "Django"]})
    competences_souhaitees: List[str] = Field(default_factory=list, json_schema_extra={"example": ["Docker", "PostgreSQL"]})
    formation_exigee: str = Field("Master / Ingénieur", json_schema_extra={"example": "Master / Ingénieur"})
    seuil_score_min: float = Field(70.0, json_schema_extra={"example": 70.0})

    @field_validator("competences_obligatoires", "competences_souhaitees", mode="before")
    @classmethod
    def _valider_competences(cls, v):
        return _normaliser_liste_competences(v)


class OffreUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    experience_min_annees: Optional[int] = None
    competences_obligatoires: Optional[List[str]] = None
    competences_souhaitees: Optional[List[str]] = None
    formation_exigee: Optional[str] = None
    seuil_score_min: Optional[float] = None
    statut: Optional[str] = None

    @field_validator("competences_obligatoires", "competences_souhaitees", mode="before")
    @classmethod
    def _valider_competences(cls, v):
        if v is None:
            return None
        return _normaliser_liste_competences(v)


class OffreResponse(OffreCreate):
    id: int
    statut: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── SCHÉMAS CANDIDAT ──

class CandidatResponse(BaseModel):
    id: int
    nom: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    cv_fichier_nom: str
    cv_chemin_stocke: Optional[str] = None   # ✅ Chemin physique du CV
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── SCHÉMAS CANDIDATURE ──

class CandidatureResponse(BaseModel):
    id: int
    offre_id: int
    candidat_id: int
    statut_ingestion: str
    score: float
    statut_ia: str
    justification_ia: Optional[str] = None
    details_scoring: Optional[Dict[str, Any]] = None
    statut: str = "EN_ATTENTE"             # ✅ Statut visible candidat
    decision_rh: str
    note_rh: Optional[str] = None
    rh_utilisateur: Optional[str] = None
    duree_traitement_sec: float
    created_at: datetime

    candidat: Optional[CandidatResponse] = None
    offre: Optional[OffreResponse] = None
    raw_ingestion_json: Optional[Dict[str, Any]] = None

    # Entretien
    date_entretien: Optional[str] = None
    format_entretien_planifie: Optional[str] = None
    lieu_entretien: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DecisionRHRequest(BaseModel):
    decision: str = Field(..., json_schema_extra={"example": "VALIDE"})
    note_rh: Optional[str] = Field(None, json_schema_extra={"example": "Candidat présélectionné."})
    rh_utilisateur: Optional[str] = Field("Recruteur RH", json_schema_extra={"example": "Sarah RH"})


# ── SCHÉMAS AUDIT ──

class AuditLogResponse(BaseModel):
    id: int
    action: str
    entite_type: str
    entite_id: Optional[int] = None
    utilisateur: str
    details: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ── SCHÉMAS AUTHENTIFICATION ──

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, json_schema_extra={"example": "recruteur"})
    password: str = Field(..., min_length=6, json_schema_extra={"example": "RecrutIA2026!"})

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── SCHÉMA CONVOCATION ENTRETIEN ──

class ConvocationRequest(BaseModel):
    date_heure: str = Field(..., json_schema_extra={"example": "Vendredi 10 Février 2026 à 14h30"})
    format_entretien: str = Field("PRESENTIEL", json_schema_extra={"example": "PRESENTIEL"})
    lieu_ou_lien: Optional[str] = Field("Bureaux ArtiWeb, Fès", json_schema_extra={"example": "Bureaux ArtiWeb, Fès"})
    message_personnalise: Optional[str] = Field(None, json_schema_extra={"example": "Merci d'apporter votre pièce d'identité."})


# ── SCHÉMA RECHERCHE CANDIDATURES PAR EMAIL ──

class CandidaturePublicResponse(BaseModel):
    """Réponse publique pour un candidat qui consulte ses candidatures."""
    id: int
    offre_titre: str
    score: float
    statut: str
    decision_rh: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)