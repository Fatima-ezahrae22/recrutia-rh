"""
Module : traiter_cv.py
Rôle   : Point d'entrée unique de la couche ingestion.
         Orchestre extraction → nettoyage → parsing → assemblage JSON.

Auteur : Agent IA RH — Couche Ingestion

Usage :
    from ingestion.traiter_cv import traiter_cv

    resultat = traiter_cv("cv_candidat.pdf")
    print(resultat)
    # {
    #     "competences": ["Python", "Django", "PostgreSQL"],
    #     "experience_annees": 4,
    #     "formation": "Master / Ingénieur",
    #     "texte_brut": "..."
    # }
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any

from ingestion.extractor import extraire_texte
from ingestion.cleaner import nettoyer_texte
from ingestion.parser import (
    extraire_competences,
    extraire_experience_annees,
    extraire_formation,
)

# ─────────────────────────────────────────
# Configuration du logging
# ─────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# Fonction principale
# ─────────────────────────────────────────

def traiter_cv(chemin_fichier: str) -> Dict[str, Any]:
    """
    Transforme un CV brut (PDF ou DOCX) en un dictionnaire structuré.

    Pipeline complet :
      ┌─────────────────────────────────────────────────────┐
      │  1. Extraction  → texte brut (PDF/DOCX/OCR)         │
      │  2. Nettoyage   → suppression bruit, normalisation   │
      │  3. Parsing     → compétences, expérience, formation │
      │  4. Assemblage  → dictionnaire JSON final            │
      └─────────────────────────────────────────────────────┘

    Args:
        chemin_fichier (str): Chemin vers le fichier CV (.pdf ou .docx).

    Returns:
        Dict avec les clés :
            - "fichier"           (str)  : nom du fichier traité
            - "competences"       (list) : liste des compétences détectées
            - "experience_annees" (int)  : années d'expérience estimées
            - "formation"         (str)  : niveau de formation le plus élevé
            - "texte_brut"        (str)  : texte nettoyé complet
            - "statut"            (str)  : "succès" ou "erreur"
            - "message"           (str)  : message informatif ou d'erreur
            - "duree_traitement"  (float): temps de traitement en secondes

    Raises:
        Ne lève pas d'exception — retourne un dict avec statut "erreur" en cas de problème.
    """
    debut = time.perf_counter()
    nom_fichier = Path(chemin_fichier).name

    logger.info("=" * 55)
    logger.info(f" TRAITEMENT CV : {nom_fichier}")
    logger.info("=" * 55)

    # Résultat de base (cas d'erreur)
    resultat_erreur = {
        "fichier": nom_fichier,
        "competences": [],
        "experience_annees": 0,
        "formation": "Non spécifié",
        "texte_brut": "",
        "statut": "erreur",
        "message": "",
        "duree_traitement": 0.0,
    }

    try:
        # ── Étape 1 : Extraction ──────────────────────────────
        logger.info("📄 Étape 1/4 — Extraction du texte")
        texte_extrait = extraire_texte(chemin_fichier)

        if not texte_extrait or len(texte_extrait.strip()) < 50:
            resultat_erreur["message"] = (
                "Extraction échouée : texte insuffisant ou fichier illisible."
            )
            return resultat_erreur

        # ── Étape 2 : Nettoyage ──────────────────────────────
        logger.info("🧹 Étape 2/4 — Nettoyage et normalisation")
        texte_propre = nettoyer_texte(texte_extrait)

        # ── Étape 3 : Parsing ────────────────────────────────
        logger.info("🔍 Étape 3/4 — Extraction des informations")
        competences      = extraire_competences(texte_propre)
        experience_annees = extraire_experience_annees(texte_propre)
        formation         = extraire_formation(texte_propre)

        # ── Étape 4 : Assemblage ─────────────────────────────
        logger.info("📦 Étape 4/4 — Assemblage du résultat")
        duree = round(time.perf_counter() - debut, 3)

        resultat = {
            "fichier":            nom_fichier,
            "competences":        competences,
            "experience_annees":  experience_annees,
            "formation":          formation,
            "texte_brut":         texte_propre,
            "statut":             "succès",
            "message":            f"CV traité avec succès ({len(competences)} compétence(s) détectée(s)).",
            "duree_traitement":   duree,
        }

        logger.info(f"✅ Traitement terminé en {duree}s")
        logger.info(f"   Compétences    : {competences}")
        logger.info(f"   Expérience     : {experience_annees} an(s)")
        logger.info(f"   Formation      : {formation}")

        return resultat

    except FileNotFoundError as e:
        resultat_erreur["message"] = f"Fichier introuvable : {e}"
        logger.error(resultat_erreur["message"])
        return resultat_erreur

    except ValueError as e:
        resultat_erreur["message"] = f"Format non supporté : {e}"
        logger.error(resultat_erreur["message"])
        return resultat_erreur

    except Exception as e:
        resultat_erreur["message"] = f"Erreur inattendue : {type(e).__name__}: {e}"
        logger.exception("Erreur non gérée dans traiter_cv()")
        return resultat_erreur

    finally:
        resultat_erreur["duree_traitement"] = round(time.perf_counter() - debut, 3)
