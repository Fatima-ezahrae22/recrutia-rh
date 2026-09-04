"""
Module : pipeline.py
Rôle   : Orchestrateur du pipeline de recrutement.
         Enchaîne :
           1. Ingestion du CV (traiter_cv)
           2. Sauvegarde permanente du fichier CV
           3. Sauvegarde du Candidat en base
           4. Évaluation IA Agentique (evaluer_candidature)
           5. Mise à jour de la Candidature + AuditLog
"""

import os
import time
import shutil
import logging
import re
import uuid
from typing import Tuple
from sqlalchemy.orm import Session

from ingestion.traiter_cv import traiter_cv
from ia_agentic.evaluer_candidature import evaluer_candidature
from backend.models import Offre, Candidat, Candidature, AuditLog

logger = logging.getLogger(__name__)

# ✅ Dossier permanent pour stocker les CVs uploadés
UPLOADS_DIR = os.path.join("uploads", "cv")
os.makedirs(UPLOADS_DIR, exist_ok=True)


def _extraire_contact_depuis_texte(texte: str) -> Tuple[str, str, str]:
    """Tente d'extraire le Nom, l'Email et le Téléphone depuis le texte du CV."""
    nom = "Candidat Anonyme"
    email = None
    tel = None

    # Extraire Email
    m_email = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", texte)
    if m_email:
        email = m_email.group(0)

    # Extraire Téléphone (format marocain ou international)
    m_tel = re.search(r"(?:\+212|0)[5-7]\d{8}", texte.replace(" ", "").replace("-", ""))
    if m_tel:
        tel = m_tel.group(0)

    # Extraire Nom (lignes initiales)
    lignes = [l.strip() for l in texte.splitlines() if len(l.strip()) > 3]
    for ligne in lignes[:5]:
        if "curriculum" not in ligne.lower() and "cv" not in ligne.lower() and "@" not in ligne:
            nom = ligne
            break

    return nom, email, tel


def _sauvegarder_cv_permanent(chemin_temp: str, nom_original: str) -> str:
    """
    Copie le CV depuis le fichier temporaire vers un dossier permanent.
    Retourne le chemin de stockage permanent.
    """
    ext = os.path.splitext(nom_original)[1].lower()
    nom_unique = f"{uuid.uuid4().hex}{ext}"
    chemin_dest = os.path.join(UPLOADS_DIR, nom_unique)
    shutil.copy2(chemin_temp, chemin_dest)
    logger.info(f"[Pipeline] CV sauvegardé : {chemin_dest}")
    return chemin_dest


def executer_pipeline_complet(
    chemin_fichier_cv: str,
    nom_original_cv: str,
    offre_id: int,
    db: Session,
    nom_candidat: str = None,
    email_candidat: str = None,
    mode_anonyme: bool = False
) -> Candidature:
    """
    Exécute le pipeline end-to-end : Ingestion ➔ Sauvegarde CV ➔ IA Agentique ➔ DB.

    Args:
        chemin_fichier_cv (str): Chemin physique du fichier CV temporaire.
        nom_original_cv (str): Nom du fichier uploadé.
        offre_id (int): Identifiant de l'offre visée.
        db (Session): Session SQLAlchemy.
        nom_candidat (str): Nom saisi manuellement (prioritaire sur extraction).
        email_candidat (str): Email saisi manuellement (prioritaire sur extraction).
        mode_anonyme (bool): Si True, anonymise le profil (Blind Recruitment).

    Returns:
        Candidature: Objet ORM Candidature complet enregistré en DB.
    """
    debut = time.perf_counter()

    # 1. Vérifier l'existence de l'offre
    offre = db.query(Offre).filter(Offre.id == offre_id).first()
    if not offre:
        raise ValueError(f"Offre ID {offre_id} introuvable en base de données.")

    logger.info(f"[Pipeline] Traitement de '{nom_original_cv}' pour l'offre '{offre.titre}' (Anonyme: {mode_anonyme})")

    # 2. ✅ Sauvegarder le CV en permanent AVANT toute suppression du temp
    chemin_cv_stocke = None
    try:
        chemin_cv_stocke = _sauvegarder_cv_permanent(chemin_fichier_cv, nom_original_cv)
    except Exception as e:
        logger.warning(f"[Pipeline] Impossible de sauvegarder le CV : {e}")

    # 3. TÂCHE 1 : Ingestion du CV
    try:
        res_ingestion = traiter_cv(chemin_fichier_cv)
    except Exception as e:
        logger.error(f"[Pipeline] Erreur ingestion CV : {e}")
        res_ingestion = {
            "statut": "erreur_ingestion",
            "texte_brut": "",
            "competences": [],
            "experience_annees": 0,
            "formation": "Non détectée",
            "erreur": str(e)
        }

    texte_cv = res_ingestion.get("texte_brut", "")

    # 4. Extraction des coordonnées depuis le texte
    nom_extrait, email_extrait, tel_cand = _extraire_contact_depuis_texte(texte_cv)

    nom_final   = nom_candidat.strip()  if nom_candidat and nom_candidat.strip()   else nom_extrait
    email_final = email_candidat.strip() if email_candidat and email_candidat.strip() else email_extrait

    if mode_anonyme:
        nom_final = f"Candidat Anonyme #{uuid.uuid4().hex[:6]}"
        tel_cand = "+212 6 ** ** ** **"

    # 5. ✅ Gestion des re-soumissions : remplacer la candidature existante
    if email_final:
        candidats_existants = db.query(Candidat).filter(Candidat.email == email_final).all()
        for cand_ex in candidats_existants:
            doublon = db.query(Candidature).filter(
                Candidature.candidat_id == cand_ex.id,
                Candidature.offre_id == offre_id
            ).first()
            if doublon:
                logger.info(f"[Pipeline] Mise à jour candidature #{doublon.id} pour {email_final}")
                db.delete(doublon)
                db.flush()  # ✅ flush avant de supprimer le candidat associé

    # 6. Créer ou mettre à jour le Candidat
    candidat_existant = None
    if email_final:
        candidat_existant = db.query(Candidat).filter(Candidat.email == email_final).first()

    if candidat_existant:
        candidat_existant.nom = nom_final
        candidat_existant.telephone = tel_cand or candidat_existant.telephone
        candidat_existant.cv_fichier_nom = nom_original_cv
        candidat_existant.cv_chemin_stocke = chemin_cv_stocke
        db.flush()
        candidat = candidat_existant
    else:
        candidat = Candidat(
            nom=nom_final,
            email=email_final,
            telephone=tel_cand,
            cv_fichier_nom=nom_original_cv,
            cv_chemin_stocke=chemin_cv_stocke
        )
        db.add(candidat)
        db.flush()  # ✅ flush pour obtenir l'ID avant de créer la Candidature

    # 7. Préparer les données offre pour la TÂCHE 2
    offre_dict_json = {
        "id": f"OFFRE_{offre.id}",
        "titre": offre.titre,
        "description": offre.description,
        "experience_min_annees": offre.experience_min_annees,
        "competences_obligatoires": offre.competences_obligatoires or [],
        "competences_souhaitees": offre.competences_souhaitees or [],
        "formation_exigee": offre.formation_exigee
    }

    # 8. TÂCHE 2 : Évaluation IA Agentique
    try:
        res_ia = evaluer_candidature(res_ingestion, offre_dict_json)
    except Exception as e:
        logger.error(f"[Pipeline] Erreur évaluation IA : {e}")
        res_ia = {
            "score": 0.0,
            "statut": "erreur_ia",
            "justification": f"Erreur lors de l'analyse IA : {str(e)}",
            "details": {}
        }

    duree_totale = round(time.perf_counter() - debut, 3)

    # 9. ✅ Créer la Candidature en DB
    candidature = Candidature(
        offre_id=offre.id,
        candidat_id=candidat.id,
        statut_ingestion=res_ingestion.get("statut", "succès"),
        raw_ingestion_json=res_ingestion,
        score=res_ia.get("score", 0.0),
        statut_ia=res_ia.get("statut", "score"),
        justification_ia=res_ia.get("justification", ""),
        details_scoring=res_ia.get("details", {}),
        statut="EN_ATTENTE",
        decision_rh="EN_ATTENTE",
        duree_traitement_sec=duree_totale
    )
    db.add(candidature)

    # 10. ✅ AuditLog
    audit = AuditLog(
        action="CANDIDATURE_SOUMISE_ET_EVALUEE",
        entite_type="Candidature",
        utilisateur="Pipeline Automatique",
        details=f"Candidature de '{candidat.nom}' ({candidat.email}) scorée {res_ia.get('score', 0)}/100 pour '{offre.titre}' (durée: {duree_totale}s)."
    )
    db.add(audit)

    # 11. ✅ Commit final avec gestion d'erreur
    try:
        db.commit()
        db.refresh(candidature)
    except Exception as e:
        db.rollback()
        logger.error(f"[Pipeline] Erreur commit DB : {e}", exc_info=True)
        raise RuntimeError(f"Erreur sauvegarde en base de données : {str(e)}")

    logger.info(f"[Pipeline] ✅ Candidature #{candidature.id} créée — {candidat.nom} — Score: {candidature.score}/100")
    return candidature
