"""
Module : routers/candidatures.py
Rôle   : Gestion des candidatures (Soumission, Scoring, Décisions RH, Export PDF, Convocation Email).
"""

import os
import json
import shutil
import tempfile
import logging
import base64
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Offre, Candidat, Candidature, AuditLog, User
from backend.schemas import (
    CandidatureResponse, DecisionRHRequest, ConvocationRequest
)
from backend.pipeline import executer_pipeline_complet
from backend.auth import get_current_user
from backend.pdf_generator import generer_pdf_candidature
from backend.email_service import envoyer_email_convocation, envoyer_email_embauche

logger = logging.getLogger("RecrutIA.CandidaturesRouter")

router = APIRouter(tags=["Candidatures"])


# ─── ENDPOINTS PUBLICS ───────────────────────────────────────────────────────

@router.post("/api/public/candidatures", response_model=CandidatureResponse, status_code=status.HTTP_201_CREATED, tags=["Public — Candidats"])
async def soumettre_candidature_publique(
    offre_id: int = Form(...),
    fichier_cv: UploadFile = File(...),
    nom_candidat: Optional[str] = Form(None),
    email_candidat: Optional[str] = Form(None),
    mode_anonyme: Optional[bool] = Form(False),
    db: Session = Depends(get_db)
):
    """
    [PUBLIC] Soumission d'un CV par un candidat sans compte.
    Pipeline : Sauvegarde CV ➔ Ingestion ➔ IA Scoring ➔ DB.
    """
    filename = fichier_cv.filename
    if not filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Format non supporté. Seuls PDF et DOCX sont acceptés.")

    ext = os.path.splitext(filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
        shutil.copyfileobj(fichier_cv.file, tmp_file)
        tmp_path = tmp_file.name

    try:
        candidature = executer_pipeline_complet(
            chemin_fichier_cv=tmp_path,
            nom_original_cv=filename,
            offre_id=offre_id,
            db=db,
            nom_candidat=nom_candidat,
            email_candidat=email_candidat,
            mode_anonyme=bool(mode_anonyme)
        )
        audit = AuditLog(
            action="CANDIDATURE_PUBLIQUE_SOUMISE",
            entite_type="Candidature",
            entite_id=candidature.id,
            utilisateur="Candidat (Public)",
            details=f"Candidature publique de '{nom_candidat or 'Anonyme'}' pour offre #{offre_id}."
        )
        db.add(audit)
        db.commit()

        # 📡 Broadcast WebSocket
        try:
            from backend.main import ws_manager
            await ws_manager.broadcast({
                "event": "NOUVELLE_CANDIDATURE",
                "candidature_id": candidature.id,
                "score": candidature.score,
                "candidat_nom": candidature.candidat.nom if candidature.candidat else "Candidat",
                "offre_titre": candidature.offre.titre if candidature.offre else "Offre",
                "message": f"Nouveau CV reçu : {candidature.candidat.nom if candidature.candidat else 'Candidat'} ({round(candidature.score)}/100)"
            })
        except Exception as ws_err:
            logger.warning(f"[WS Broadcast Error] {ws_err}")

        return candidature
    except ValueError as ve:
        msg = str(ve)
        if "DOUBLON_DETECTE" in msg:
            raise HTTPException(status_code=400, detail=msg.replace("DOUBLON_DETECTE: ", ""))
        raise HTTPException(status_code=404, detail=msg)
    except Exception as e:
        logger.error(f"[API Public] Erreur : {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur traitement CV : {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


from datetime import datetime
from sqlalchemy.orm.attributes import flag_modified

@router.get("/api/public/candidatures", tags=["Public — Candidats"])
def historique_candidatures_public(email: str, db: Session = Depends(get_db)):
    """
    [PUBLIC] Historique des candidatures d'un candidat par email.
    """
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Email invalide.")

    candidat = db.query(Candidat).filter(Candidat.email == email).first()
    if not candidat:
        raise HTTPException(status_code=404, detail="Aucune candidature trouvée pour cet email.")

    candidatures = db.query(Candidature).filter(
        Candidature.candidat_id == candidat.id
    ).order_by(Candidature.created_at.desc()).all()

    result = []
    for c in candidatures:
        details_sc = c.details_scoring or {}
        conseils = details_sc.get("conseils_ia", [])

        # Détermination exacte du statut d'embauche ou de sélection
        statut_final = c.statut or "EN_ATTENTE"
        if c.decision_rh in ["EMBAUCHE", "EMBAUCHE_CONFIRME"]:
            statut_final = "EMBAUCHE"
        elif c.decision_rh in ["VALIDE", "ACCEPT"]:
            statut_final = "ACCEPTE"
        elif c.decision_rh in ["REJETE", "REFUSE"]:
            statut_final = "REFUSE"

        # Construction de la timeline d'avancement
        timeline = [
            {"etape": "Soumission CV", "statut": "TERMINE", "description": f"CV reçu le {c.created_at.strftime('%d/%m/%Y à %H:%M') if c.created_at else ''}"},
            {"etape": "Évaluation IA", "statut": "TERMINE", "description": f"Score calculé: {round(c.score)}/100"},
        ]

        if c.decision_rh in ["EMBAUCHE", "EMBAUCHE_CONFIRME"]:
            timeline.append({"etape": "Décision RH", "statut": "TERMINE", "description": "🎉 Candidat embauché et confirmé !"})
        elif c.decision_rh in ["VALIDE", "REJETE"]:
            timeline.append({"etape": "Revue RH", "statut": "TERMINE", "description": f"Décision RH enregistrée : {c.decision_rh}"})
        else:
            timeline.append({"etape": "Revue RH", "statut": "EN_COURS", "description": "Examen en cours par l'équipe RH ArtiWeb"})

        if c.date_entretien:
            timeline.append({"etape": "Entretien", "statut": "PLANIFIE", "description": f"Prévu le {c.date_entretien} ({c.format_entretien_planifie or 'Présentiel'})"})

        result.append({
            "id": c.id,
            "offre_titre": c.offre.titre if c.offre else "Offre d'emploi",
            "offre_id": c.offre_id,
            "score": c.score,
            "statut": statut_final,
            "decision_rh": c.decision_rh,
            "date_entretien": c.date_entretien,
            "format_entretien": c.format_entretien_planifie,
            "lieu_entretien": c.lieu_entretien,
            "justification_ia": c.justification_ia,
            "conseils_ia": conseils,
            "timeline": timeline,
            "confirmation_entretien": details_sc.get("confirmation_entretien"),
            "messages_candidat": details_sc.get("messages_candidat", []),
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return result


from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Body

@router.post("/api/public/candidatures/{candidature_id}/confirmer-entretien", tags=["Public — Candidats"])
def confirmer_entretien_public(
    candidature_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """[PUBLIC] Confirmation ou demande de report d'entretien par le candidat."""
    cand = db.query(Candidature).filter(Candidature.id == candidature_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidature introuvable.")

    choix = payload.get("choix", "CONFIRME")
    msg_opt = payload.get("message", "")

    dt = cand.details_scoring or {}
    dt["confirmation_entretien"] = {
        "statut": choix,
        "date_reponse": datetime.utcnow().strftime("%d/%m/%Y à %H:%M"),
        "message": msg_opt
    }
    cand.details_scoring = dt
    flag_modified(cand, "details_scoring")

    candidat_nom = cand.candidat.nom if cand.candidat else "Un candidat"
    action_log = "a confirmé sa présence à l'entretien" if choix == "CONFIRME" else "a demandé un report d'entretien"

    log = AuditLog(
        utilisateur=candidat_nom,
        action=f"Réponse Entretien : {action_log}",
        entite_type="candidature",
        entite_id=cand.id,
        details=json.dumps({"candidature_id": cand.id, "email": cand.candidat.email if cand.candidat else "", "note": msg_opt})
    )
    db.add(log)
    db.commit()

    return {"message": "Votre réponse a été enregistrée et transmise à l'équipe RH.", "confirmation": dt["confirmation_entretien"]}


@router.post("/api/public/candidatures/{candidature_id}/message", tags=["Public — Candidats"])
def envoyer_message_rh_public(
    candidature_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """[PUBLIC] Messagerie Candidat -> Envoi d'une question/message à l'équipe RH."""
    cand = db.query(Candidature).filter(Candidature.id == candidature_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidature introuvable.")

    texte = payload.get("message", "").strip()
    if not texte:
        raise HTTPException(status_code=400, detail="Le message ne peut pas être vide.")

    dt = cand.details_scoring or {}
    msgs = dt.get("messages_candidat", [])
    candidat_nom = cand.candidat.nom if cand.candidat else "Candidat"
    
    nouveau = {
        "expediteur": candidat_nom,
        "texte": texte,
        "date": datetime.utcnow().strftime("%d/%m/%Y à %H:%M")
    }
    msgs.append(nouveau)
    dt["messages_candidat"] = msgs
    cand.details_scoring = dt
    flag_modified(cand, "details_scoring")

    log = AuditLog(
        utilisateur=candidat_nom,
        action="Question / Message Candidat RH",
        entite_type="candidature",
        entite_id=cand.id,
        details=json.dumps({"candidature_id": cand.id, "message": texte})
    )
    db.add(log)
    return {"message": "Votre question a été transmise à l'équipe RH avec succès.", "messages": msgs}


@router.post("/api/candidatures/{candidature_id}/repondre-message", tags=["Candidatures"])
def repondre_message_candidat_rh(
    candidature_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """[RH] Répondre directement au message / question posée par un candidat."""
    cand = db.query(Candidature).filter(Candidature.id == candidature_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidature introuvable.")

    texte = payload.get("message", "").strip()
    if not texte:
        raise HTTPException(status_code=400, detail="Le message ne peut pas être vide.")

    dt = cand.details_scoring or {}
    msgs = dt.get("messages_candidat", [])
    
    nouveau = {
        "expediteur": f"Équipe RH ({current_user.username})",
        "texte": texte,
        "date": datetime.utcnow().strftime("%d/%m/%Y à %H:%M"),
        "is_rh": True
    }
    msgs.append(nouveau)
    dt["messages_candidat"] = msgs
    cand.details_scoring = dt
    flag_modified(cand, "details_scoring")

    log = AuditLog(
        utilisateur=current_user.username,
        action="Réponse RH à la question du Candidat",
        entite_type="candidature",
        entite_id=cand.id,
        details=json.dumps({"candidature_id": cand.id, "reponse": texte})
    )
    db.add(log)
    db.commit()

    return {"message": "Réponse RH transmise au candidat avec succès.", "messages": msgs}


# ─── ENDPOINTS RH PROTÉGÉS ───────────────────────────────────────────────────

@router.post("/api/candidatures", response_model=CandidatureResponse, status_code=status.HTTP_201_CREATED, tags=["Candidatures"])
async def soumettre_candidature(
    offre_id: int = Form(...),
    fichier_cv: UploadFile = File(...),
    nom_candidat: Optional[str] = Form(None),
    email_candidat: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """[RH] Soumettre un CV pour une offre (pipeline complet)."""
    filename = fichier_cv.filename
    if not filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF et DOCX sont acceptés.")

    ext = os.path.splitext(filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
        shutil.copyfileobj(fichier_cv.file, tmp_file)
        tmp_path = tmp_file.name

    try:
        candidature = executer_pipeline_complet(
            chemin_fichier_cv=tmp_path,
            nom_original_cv=filename,
            offre_id=offre_id,
            db=db,
            nom_candidat=nom_candidat,
            email_candidat=email_candidat
        )
        audit = AuditLog(
            action="CV_SOUMIS_PAR_RH",
            entite_type="Candidature",
            entite_id=candidature.id,
            utilisateur=current_user.username,
            details=f"CV soumis par RH '{current_user.username}' pour offre #{offre_id}."
        )
        db.add(audit)
        db.commit()

        # 📡 Broadcast WebSocket
        try:
            from backend.main import ws_manager
            await ws_manager.broadcast({
                "event": "NOUVELLE_CANDIDATURE",
                "candidature_id": candidature.id,
                "score": candidature.score,
                "candidat_nom": candidature.candidat.nom if candidature.candidat else "Candidat",
                "offre_titre": candidature.offre.titre if candidature.offre else "Offre",
                "message": f"Nouveau CV ingéré : {candidature.candidat.nom if candidature.candidat else 'Candidat'} ({round(candidature.score)}/100)"
            })
        except Exception as ws_err:
            logger.warning(f"[WS Broadcast Error] {ws_err}")

        return candidature
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except RuntimeError as re_:
        raise HTTPException(status_code=500, detail=str(re_))
    except Exception as e:
        logger.error(f"[API] Erreur candidature : {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur traitement CV : {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.get("/api/candidatures/toutes", response_model=List[CandidatureResponse], tags=["Candidatures"])
def toutes_candidatures(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """[RH] Toutes les candidatures, triées par score décroissant."""
    return db.query(Candidature).order_by(Candidature.score.desc()).all()


@router.get("/api/offres/{offre_id}/candidatures", response_model=List[CandidatureResponse], tags=["Candidatures"])
def lister_candidatures_offre(offre_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Candidatures pour une offre donnée, triées par score."""
    offre = db.query(Offre).filter(Offre.id == offre_id).first()
    if not offre:
        raise HTTPException(status_code=404, detail=f"Offre ID {offre_id} introuvable.")
    return (
        db.query(Candidature)
        .filter(Candidature.offre_id == offre_id)
        .order_by(Candidature.score.desc())
        .all()
    )


@router.get("/api/candidatures/{candidature_id}", response_model=CandidatureResponse, tags=["Candidatures"])
def obtenir_candidature(candidature_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fiche complète d'une candidature."""
    cand = db.query(Candidature).filter(Candidature.id == candidature_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail=f"Candidature ID {candidature_id} introuvable.")
    return cand


def generer_cv_fallback_pdf(candidat, cand, path_destination):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(path_destination, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []
        styles = getSampleStyleSheet()

        primary = colors.HexColor("#1E1B4B")
        accent = colors.HexColor("#4F46E5")
        text_dark = colors.HexColor("#0F172A")

        title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=20, textColor=primary, spaceAfter=4)
        sub_style = ParagraphStyle('SubTitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor("#64748B"), spaceAfter=12)
        section_style = ParagraphStyle('SecTitle', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=13, textColor=accent, spaceBefore=10, spaceAfter=6)
        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=text_dark, leading=14)

        raw = cand.raw_ingestion_json if cand and cand.raw_ingestion_json else {}
        nom = candidat.nom if candidat and candidat.nom else "Candidat RecrutIA"
        email = candidat.email if candidat and candidat.email else "candidat@email.com"
        tel = candidat.telephone if candidat and candidat.telephone else "Non renseigné"
        
        exp_val = raw.get("experience_annees")
        exp = f"{exp_val} ans" if exp_val is not None else "Non spécifié"
        diplome = raw.get("formation") or "Master / Ingénieur"

        story.append(Paragraph(f"<b>{nom}</b>", title_style))
        story.append(Paragraph(f"<b>Email :</b> {email} &nbsp;|&nbsp; <b>Tél :</b> {tel} &nbsp;|&nbsp; <b>Expérience :</b> {exp}", sub_style))
        story.append(HRFlowable(width="100%", thickness=2, color=accent, spaceBefore=0, spaceAfter=12))

        story.append(Paragraph("🎓 Diplôme & Formation", section_style))
        story.append(Paragraph(f"• <b>Niveau / Diplôme :</b> {diplome}", body_style))
        story.append(Spacer(1, 8))

        story.append(Paragraph("⚡ Compétences Clés Extrait du CV", section_style))
        comps = raw.get("competences") or ["Python", "FastAPI", "React", "SQL"]
        comp_str = " • ".join(comps) if isinstance(comps, list) else str(comps)
        story.append(Paragraph(f"<b>Compétences détectées :</b> {comp_str}", body_style))
        story.append(Spacer(1, 8))

        if cand:
            story.append(Paragraph("🎯 Adéquation Poste & Synthèse IA", section_style))
            score_val = cand.score if cand.score else 80.0
            offre_titre = cand.offre.titre if cand and cand.offre else "Offre d'emploi"
            story.append(Paragraph(f"• <b>Poste visé :</b> {offre_titre}", body_style))
            story.append(Paragraph(f"• <b>Score d'adéquation sémantique IA :</b> {round(score_val)}%", body_style))
            if cand.justification_ia:
                story.append(Spacer(1, 4))
                story.append(Paragraph(f"• <b>Évaluation sémantique :</b> {cand.justification_ia}", body_style))

        doc.build(story)
        return True
    except Exception as e:
        logger.error(f"[PDF Fallback Error] {e}", exc_info=True)
        return False


@router.get("/api/candidatures/{candidature_id}/cv", tags=["Candidatures"])
def telecharger_cv_original(
    candidature_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Télécharger le fichier CV original exact d'un candidat."""
    cand = db.query(Candidature).filter(Candidature.id == candidature_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail=f"Candidature ID {candidature_id} introuvable.")

    candidat = cand.candidat
    if not candidat:
        raise HTTPException(status_code=404, detail="Dossier candidat non disponible pour cette candidature.")

    nom_fichier = candidat.cv_fichier_nom or f"CV_{candidat.nom or candidat.id}.pdf"

    # 1. ✅ Tenter la restitution exacte depuis la Base64 stockée en base de données (100% permanent sur Vercel)
    if candidat.cv_base64:
        try:
            content_bytes = base64.b64decode(candidat.cv_base64)
            media_type = "application/pdf"
            if nom_fichier.lower().endswith(".docx"):
                media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            return Response(
                content=content_bytes,
                media_type=media_type,
                headers={"Content-Disposition": f'inline; filename="{nom_fichier}"'}
            )
        except Exception as err_dec:
            logger.warning(f"[CV Base64 Decode Error] {err_dec}")

    # 2. ✅ Tenter de lire le fichier physique local sur le serveur
    chemin_cv = candidat.cv_chemin_stocke
    if chemin_cv and os.path.exists(chemin_cv):
        return FileResponse(
            chemin_cv,
            filename=nom_fichier,
            media_type="application/pdf"
        )

    # 3. Fallback de secours ultime si aucune copie n'est disponible
    tmp_dir = os.path.join(tempfile.gettempdir(), "uploads", "cv")
    os.makedirs(tmp_dir, exist_ok=True)
    fallback_path = os.path.join(tmp_dir, f"CV_Gen_{candidat.id}.pdf")
    ok = generer_cv_fallback_pdf(candidat, cand, fallback_path)
    if ok and os.path.exists(fallback_path):
        return FileResponse(
            fallback_path,
            filename=nom_fichier,
            media_type="application/pdf"
        )

    raise HTTPException(status_code=404, detail="Fichier CV non disponible sur le serveur.")


@router.get("/api/candidatures/{candidature_id}/pdf", tags=["Candidatures"])
def telecharger_pdf_candidature(
    candidature_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Télécharger le rapport d'évaluation RH au format PDF."""
    cand = db.query(Candidature).filter(Candidature.id == candidature_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail=f"Candidature ID {candidature_id} introuvable.")

    candidat_nom = cand.candidat.nom if cand.candidat and cand.candidat.nom else (cand.candidat.cv_fichier_nom if cand.candidat else "Candidat")
    offre_titre = cand.offre.titre if cand.offre else "Offre d'emploi"

    candidature_dict = {
        "score": cand.score,
        "decision_rh": cand.decision_rh,
        "justification_ia": cand.justification_ia,
        "note_rh": cand.note_rh,
        "raw_ingestion_json": cand.raw_ingestion_json or {}
    }

    pdf_path = generer_pdf_candidature(candidature_dict, candidat_nom, offre_titre)
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"Rapport_RecrutIA_{candidature_id}.pdf")


@router.patch("/api/candidatures/{candidature_id}/decision", response_model=CandidatureResponse, tags=["Supervision RH"])
async def enregistrer_decision_rh(
    candidature_id: int,
    decision_in: DecisionRHRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enregistrer la décision RH sur une candidature et mettre à jour le statut candidat."""
    candidature = db.query(Candidature).filter(Candidature.id == candidature_id).first()
    if not candidature:
        raise HTTPException(status_code=404, detail=f"Candidature ID {candidature_id} introuvable.")

    decision_norm = decision_in.decision.upper()
    if decision_norm not in ["VALIDE", "CORRIGE", "REJETE", "EMBAUCHE", "REJETE_POST_ENTRETIEN", "PASSE"]:
        raise HTTPException(status_code=400, detail="Décision invalide.")

    candidature.decision_rh = decision_norm
    candidature.note_rh = decision_in.note_rh
    candidature.rh_utilisateur = current_user.username

    if decision_norm in ["VALIDE", "EMBAUCHE"]:
        candidature.statut = "ACCEPTE"
    elif decision_norm in ["REJETE", "REJETE_POST_ENTRETIEN"]:
        candidature.statut = "REFUSE"
    else:
        candidature.statut = "EN_ATTENTE"

    audit = AuditLog(
        action=f"DECISION_RH_{decision_norm}",
        entite_type="Candidature", entite_id=candidature.id,
        utilisateur=current_user.username,
        details=f"Décision '{decision_norm}' pour Candidature #{candidature.id}. Note: {decision_in.note_rh or 'Aucune'}."
    )
    db.add(audit)
    db.commit()
    db.refresh(candidature)
    logger.info(f"[API] ✅ Décision RH '{decision_norm}' → Candidature #{candidature.id} — Statut : {candidature.statut}")

    # 📡 Broadcast WebSocket
    try:
        from backend.main import ws_manager
        await ws_manager.broadcast({
            "event": "DECISION_RH_MISE_A_JOUR",
            "candidature_id": candidature.id,
            "decision": decision_norm,
            "statut": candidature.statut,
            "candidat_nom": candidature.candidat.nom if candidature.candidat else "Candidat",
            "message": f"Décision RH mise à jour : {candidature.candidat.nom if candidature.candidat else 'Candidat'} ➔ {decision_norm}"
        })
    except Exception as ws_err:
        logger.warning(f"[WS Broadcast Error] {ws_err}")

    # ── Auto-envoi email embauche si candidat retenu ─────────────────────────
    if decision_norm == "EMBAUCHE":
        try:
            candidat_nom   = candidature.candidat.nom if candidature.candidat and candidature.candidat.nom else (candidature.candidat.cv_fichier_nom if candidature.candidat else "Candidat")
            candidat_email = candidature.candidat.email if candidature.candidat and candidature.candidat.email else None
            offre_titre    = candidature.offre.titre if candidature.offre else "Offre d'emploi"
            if candidat_email:
                res_email = envoyer_email_embauche(
                    destinataire_email=candidat_email,
                    nom_candidat=candidat_nom,
                    titre_offre=offre_titre,
                    note_rh=decision_in.note_rh,
                    score_ia=candidature.score
                )
                audit_email = AuditLog(
                    action="EMAIL_EMBAUCHE_ENVOYE",
                    entite_type="Candidature",
                    entite_id=candidature.id,
                    utilisateur=current_user.username,
                    details=f"Email embauche envoyé à '{candidat_nom}' ({candidat_email}) — Mode: {res_email.get('mode', '?')}."
                )
                db.add(audit_email)
                db.commit()
                logger.info(f"[API] 📧 Email embauche → {candidat_email} ({res_email.get('mode')})")
        except Exception as e:
            logger.error(f"[API] Erreur envoi email embauche : {e}")

    return candidature


@router.post("/api/candidatures/{candidature_id}/convocation", tags=["Supervision RH"])
def convoquer_candidat_entretien(
    candidature_id: int,
    conv_in: ConvocationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Convoquer un candidat à un entretien et lui envoyer un email."""
    cand = db.query(Candidature).filter(Candidature.id == candidature_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail=f"Candidature ID {candidature_id} introuvable.")

    candidat_nom = cand.candidat.nom if cand.candidat and cand.candidat.nom else (cand.candidat.cv_fichier_nom if cand.candidat else "Candidat")
    candidat_email = cand.candidat.email if cand.candidat and cand.candidat.email else "candidat@email.com"
    offre_titre = cand.offre.titre if cand.offre else "Offre d'emploi"

    cand.decision_rh = "VALIDE"
    cand.statut = "ACCEPTE"
    cand.rh_utilisateur = current_user.username
    cand.date_entretien = conv_in.date_heure
    cand.format_entretien_planifie = conv_in.format_entretien
    cand.lieu_entretien = conv_in.lieu_ou_lien

    res_email = envoyer_email_convocation(
        destinataire_email=candidat_email,
        nom_candidat=candidat_nom,
        titre_offre=offre_titre,
        date_heure=conv_in.date_heure,
        format_entretien=conv_in.format_entretien,
        lieu_ou_lien=conv_in.lieu_ou_lien,
        message_personnalise=conv_in.message_personnalise
    )

    audit = AuditLog(
        action="CONVOCATION_ENTRETIEN_ENVOYEE",
        entite_type="Candidature",
        entite_id=cand.id,
        utilisateur=current_user.username,
        details=f"Convocation envoyée à '{candidat_nom}' ({candidat_email}) pour le {conv_in.date_heure}."
    )
    db.add(audit)
    db.commit()
    db.refresh(cand)

    return {
        "statut": "succes",
        "message": f"Convocation transmise avec succès à {candidat_email}.",
        "candidature_id": cand.id,
        "email_details": res_email
    }
