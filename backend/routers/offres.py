"""
Module : routers/offres.py
Rôle   : Gestion des offres d'emploi (Publiques et protégees RH).
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Offre, AuditLog, User
from backend.schemas import OffreCreate, OffreUpdate, OffreResponse
from backend.auth import get_current_user

logger = logging.getLogger("RecrutIA.OffresRouter")

router = APIRouter(tags=["Offres d'emploi"])


# ─── ENDPOINTS PUBLICS ───────────────────────────────────────────────────────

@router.get("/api/public/offres", response_model=List[OffreResponse], tags=["Public — Candidats"])
def lister_offres_publiques(db: Session = Depends(get_db)):
    """[PUBLIC] Lister toutes les offres actives."""
    return db.query(Offre).filter(Offre.statut == "ACTIF").order_by(Offre.created_at.desc()).all()


@router.get("/api/public/offres/{offre_id}", response_model=OffreResponse, tags=["Public — Candidats"])
def obtenir_offre_publique(offre_id: int, db: Session = Depends(get_db)):
    """[PUBLIC] Détails d'une offre active."""
    offre = db.query(Offre).filter(Offre.id == offre_id, Offre.statut == "ACTIF").first()
    if not offre:
        raise HTTPException(status_code=404, detail=f"Offre ID {offre_id} introuvable ou inactive.")
    return offre


# ─── ENDPOINTS RH PROTÉGÉS ───────────────────────────────────────────────────

@router.post("/api/offres", response_model=OffreResponse, status_code=status.HTTP_201_CREATED, tags=["Offres d'emploi"])
async def creer_offre(offre_in: OffreCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Création d'une nouvelle offre d'emploi."""
    nouvelle_offre = Offre(
        titre=offre_in.titre,
        description=offre_in.description,
        experience_min_annees=offre_in.experience_min_annees,
        competences_obligatoires=offre_in.competences_obligatoires,
        competences_souhaitees=offre_in.competences_souhaitees,
        formation_exigee=offre_in.formation_exigee,
        seuil_score_min=offre_in.seuil_score_min or 70.0,
        statut="ACTIF"
    )
    db.add(nouvelle_offre)
    db.commit()
    db.refresh(nouvelle_offre)
    audit = AuditLog(
        action="OFFRE_CREEE", entite_type="Offre", entite_id=nouvelle_offre.id,
        utilisateur=current_user.username,
        details=f"Offre #{nouvelle_offre.id} '{nouvelle_offre.titre}' créée."
    )
    db.add(audit)
    db.commit()
    logger.info(f"[API] ✅ Offre créée ID #{nouvelle_offre.id} — '{nouvelle_offre.titre}'")

    # 📡 Broadcast WebSocket
    try:
        from backend.main import ws_manager
        await ws_manager.broadcast({
            "event": "NOUVELLE_OFFRE",
            "offre_id": nouvelle_offre.id,
            "titre": nouvelle_offre.titre,
            "seuil_score_min": nouvelle_offre.seuil_score_min,
            "message": f"Nouvelle offre publiée : {nouvelle_offre.titre}"
        })
    except Exception as ws_err:
        logger.warning(f"[WS Broadcast Error] {ws_err}")

    return nouvelle_offre


@router.get("/api/offres", response_model=List[OffreResponse], tags=["Offres d'emploi"])
def lister_offres(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lister toutes les offres d'emploi (RH)."""
    return db.query(Offre).order_by(Offre.created_at.desc()).all()


@router.get("/api/offres/{offre_id}", response_model=OffreResponse, tags=["Offres d'emploi"])
def obtenir_offre(offre_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Détails d'une offre d'emploi."""
    offre = db.query(Offre).filter(Offre.id == offre_id).first()
    if not offre:
        raise HTTPException(status_code=404, detail=f"Offre ID {offre_id} introuvable.")
    return offre


@router.put("/api/offres/{offre_id}", response_model=OffreResponse, tags=["Offres d'emploi"])
def modifier_offre(offre_id: int, offre_in: OffreUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Modifier une offre d'emploi existante."""
    offre = db.query(Offre).filter(Offre.id == offre_id).first()
    if not offre:
        raise HTTPException(status_code=404, detail=f"Offre ID {offre_id} introuvable.")

    if offre_in.titre is not None: offre.titre = offre_in.titre
    if offre_in.description is not None: offre.description = offre_in.description
    if offre_in.experience_min_annees is not None: offre.experience_min_annees = offre_in.experience_min_annees
    if offre_in.competences_obligatoires is not None: offre.competences_obligatoires = offre_in.competences_obligatoires
    if offre_in.competences_souhaitees is not None: offre.competences_souhaitees = offre_in.competences_souhaitees
    if offre_in.formation_exigee is not None: offre.formation_exigee = offre_in.formation_exigee
    if offre_in.seuil_score_min is not None: offre.seuil_score_min = offre_in.seuil_score_min
    if offre_in.statut is not None: offre.statut = offre_in.statut

    db.commit()
    db.refresh(offre)

    audit = AuditLog(
        action="OFFRE_MODIFIEE", entite_type="Offre", entite_id=offre.id,
        utilisateur=current_user.username,
        details=f"Offre #{offre.id} '{offre.titre}' modifiée."
    )
    db.add(audit)
    db.commit()
    logger.info(f"[API] ✅ Offre modifiée ID #{offre.id}")
    return offre


@router.delete("/api/offres/{offre_id}", tags=["Offres d'emploi"])
def supprimer_offre(offre_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Supprimer une offre et toutes ses candidatures associées."""
    offre = db.query(Offre).filter(Offre.id == offre_id).first()
    if not offre:
        raise HTTPException(status_code=404, detail=f"Offre ID {offre_id} introuvable.")

    titre = offre.titre
    db.delete(offre)
    db.commit()

    audit = AuditLog(
        action="OFFRE_SUPPRIMEE", entite_type="Offre", entite_id=offre_id,
        utilisateur=current_user.username,
        details=f"Offre #{offre_id} '{titre}' supprimée."
    )
    db.add(audit)
    db.commit()
    logger.info(f"[API] ✅ Offre supprimée ID #{offre_id}")
    return {"detail": f"Offre '{titre}' supprimée avec succès.", "id": offre_id}
