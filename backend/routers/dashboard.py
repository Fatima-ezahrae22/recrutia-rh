"""
Module : routers/dashboard.py
Rôle   : Statistiques globales, entretiens planifiés, suppression d'entretiens et logs d'audit.
"""

import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Offre, Candidature, AuditLog, User
from backend.schemas import AuditLogResponse
from backend.auth import get_current_user

logger = logging.getLogger("RecrutIA.DashboardRouter")

router = APIRouter(tags=["Supervision RH"])


@router.get("/api/stats")
def obtenir_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Statistiques globales pour le tableau de bord RH."""
    nb_offres = db.query(Offre).filter(Offre.statut == "ACTIF").count()
    nb_candidatures = db.query(Candidature).count()
    nb_entretiens = db.query(Candidature).filter(Candidature.date_entretien != None).count()
    nb_valides = db.query(Candidature).filter(Candidature.decision_rh == "VALIDE").count()
    nb_rejetes = db.query(Candidature).filter(Candidature.decision_rh == "REJETE").count()
    nb_attente = db.query(Candidature).filter(Candidature.decision_rh == "EN_ATTENTE").count()

    return {
        "offres_actives": nb_offres,
        "candidatures_total": nb_candidatures,
        "entretiens_planifies": nb_entretiens,
        "candidatures_validees": nb_valides,
        "candidatures_rejetees": nb_rejetes,
        "candidatures_en_attente": nb_attente,
    }


@router.get("/api/entretiens")
def lister_entretiens(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Tous les entretiens planifiés."""
    candidatures = (
        db.query(Candidature)
        .filter(Candidature.date_entretien != None)
        .order_by(Candidature.date_entretien.asc())
        .all()
    )
    result = []
    for c in candidatures:
        nom = c.candidat.nom if c.candidat and c.candidat.nom else "Candidat"
        email = c.candidat.email if c.candidat else ""
        offre_titre = c.offre.titre if c.offre else "Offre"
        result.append({
            "candidature_id": c.id,
            "candidat_nom": nom,
            "candidat_email": email,
            "offre_titre": offre_titre,
            "offre_id": c.offre_id,
            "score_ia": c.score,
            "date_entretien": c.date_entretien,
            "format_entretien": c.format_entretien_planifie or "PRESENTIEL",
            "lieu_entretien": c.lieu_entretien or "",
            "rh_utilisateur": c.rh_utilisateur or "Recruteur",
            "decision_rh": c.decision_rh,
        })
    return result


@router.delete("/api/entretiens/{candidature_id}")
def annuler_entretien(candidature_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Annuler et supprimer un entretien planifié du calendrier."""
    c = db.query(Candidature).filter(Candidature.id == candidature_id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entretien introuvable.")
    
    c.date_entretien = None
    c.format_entretien_planifie = None
    c.lieu_entretien = None
    
    audit = AuditLog(
        utilisateur=current_user.username,
        action="SUPPRESSION_ENTRETIEN",
        details={"candidature_id": candidature_id}
    )
    db.add(audit)
    db.commit()
    
    return {"message": f"Entretien #{candidature_id} supprimé du calendrier."}


@router.get("/api/audit", response_model=List[AuditLogResponse], tags=["Audit & Traçabilité"])
def lister_logs_audit(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Journal d'audit de toutes les actions système et RH."""
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()


@router.get("/api/candidatures/export/csv")
def exporter_candidatures_csv(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Exporte la liste de toutes les candidatures et évaluations IA au format CSV (Excel)."""
    candidatures = db.query(Candidature).order_by(Candidature.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["ID", "Nom Candidat", "Email", "Offre", "Score IA (%)", "Statut RH", "Date Entretien", "Lieu / Lien Entretien", "Date Dépôt"])
    
    for c in candidatures:
        nom = c.candidat.nom if c.candidat else "Candidat"
        email = c.candidat.email if c.candidat else ""
        offre_titre = c.offre.titre if c.offre else ""
        writer.writerow([
            c.id,
            nom,
            email,
            offre_titre,
            f"{c.score:.1f}",
            c.decision_rh,
            c.date_entretien or "",
            c.lieu_entretien or "",
            c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else ""
        ])
    
    csv_content = output.getvalue().encode('utf-8-sig')  # UTF-8 BOM pour Excel
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=recrutia_export_candidatures.csv"}
    )
