"""
Module : evaluer_candidature.py
Rôle   : Orchestrateur central de la Couche IA Agentique (Couche 2).
         Enchaîne :
           1. Filtre sur critères durs (hard_filter)
           2. Embeddings & similarité cosinus (embeddings_scorer)
           3. Génération de la justification LLM (llm_justifier)

Auteur : Agent IA RH — Couche IA Agentique
"""

import time
import logging
from typing import Dict, Any

from ia_agentic.hard_filter import verifier_criteres_durs
from ia_agentic.embeddings_scorer import calculer_score_semantique
from ia_agentic.llm_justifier import generer_justification

logger = logging.getLogger(__name__)


def evaluer_candidature(candidat: Dict[str, Any], offre: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fonction principale de la Couche IA Agentique.
    Évalue l'adéquation d'un candidat structuré par rapport à une offre d'emploi.

    Contrat de sortie :
        {
            "score": float,            # ex: 85.5 (ou 0.0 si rejeté d'entrée)
            "justification": str,      # explication rédigée et fiable du score
            "statut": str,             # "score" ou "rejete_auto_filtre"
            "details": dict,           # sous-scores vectoriel, compétences, expérience
            "duree_evaluation": float  # temps d'exécution en secondes
        }

    Args:
        candidat (Dict[str, Any]): Dictionnaire du candidat (sortie de la couche ingestion).
        offre (Dict[str, Any]): Dictionnaire de l'offre d'emploi.

    Returns:
        Dict[str, Any]: Résultat complet de l'évaluation scorée.
    """
    debut = time.perf_counter()

    nom_candidat = candidat.get("fichier", "Candidat")
    titre_offre  = offre.get("titre", "Offre d'emploi")

    logger.info("=" * 60)
    logger.info(f" ÉVALUATION IA AGENTIQUE : {nom_candidat} ➔ '{titre_offre}'")
    logger.info("=" * 60)

    # ── ÉTAPE 1 : Filtre sur critères durs ──
    valide_criteres_durs, raison_rejet = verifier_criteres_durs(candidat, offre)

    if not valide_criteres_durs:
        duree = round(time.perf_counter() - debut, 3)
        justification_rejet = (
            f"CANDIDATURE REJETÉE PAR LE FILTRE AUTOMATIQUE CRITÈRES DURS.\n"
            f"Offre : '{titre_offre}'\n"
            f"Motif du rejet : {raison_rejet}\n"
            f"Aucun calcul sémantique approfondi n'a été effectué."
        )

        logger.warning(f"❌ REJET AUTOMATIQUE : {nom_candidat} — {raison_rejet}")

        return {
            "score": 0.0,
            "justification": justification_rejet,
            "statut": "rejete_auto_filtre",
            "details": {
                "motif_rejet": raison_rejet,
                "score_vectoriel_pct": 0.0,
                "score_competences_pct": 0.0,
                "score_experience_pct": 0.0,
                "competences_presentes": [],
                "competences_manquantes": offre.get("competences_obligatoires", [])
            },
            "duree_evaluation": duree
        }

    # ── ÉTAPE 2 & 3 : Vectorisation & Calcul du Score Sémantique ──
    logger.info("🧠 Étape 2/3 — Calcul de la similarité sémantique & vectorielle...")
    score_final, details = calculer_score_semantique(candidat, offre)

    # ── ÉTAPE 4 : Génération de la Justification Argumentée (LLM) ──
    logger.info("📝 Étape 3/3 — Génération de la justification argumentée...")
    justification = generer_justification(candidat, offre, score_final, details)

    duree = round(time.perf_counter() - debut, 3)

    logger.info(f"✅ ÉVALUATION TERMINÉE en {duree}s — Score: {score_final}/100 — Statut: 'score'")

    return {
        "score": score_final,
        "justification": justification,
        "statut": "score",
        "details": details,
        "duree_evaluation": duree
    }
