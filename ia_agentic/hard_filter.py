"""
Module : hard_filter.py
Rôle   : Étape 1 de la Couche IA Agentique.
         Filtre les candidatures sur les critères durs non négociables
         (expérience minimale exigée, compétences obligatoires).

Auteur : Agent IA RH — Couche IA Agentique
"""

import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


def verifier_criteres_durs(candidat: Dict[str, Any], offre: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Vérifie si le candidat remplit les critères obligatoires (durs) de l'offre.

    Critères examinés :
      1. Expérience minimale (en années)
      2. Compétences obligatoires (doit posséder au moins les compétences essentielles exigées)

    Args:
        candidat (Dict[str, Any]): JSON structuré du candidat (sortie de la couche ingestion).
        offre (Dict[str, Any]): JSON structuré de l'offre d'emploi.

    Returns:
        Tuple[bool, str]:
            - bool : True si le candidat passe le filtre dur, False sinon.
            - str  : Motif détaillé d'acceptation ou de rejet.
    """
    nom_candidat = candidat.get("fichier", "Candidat")
    titre_offre  = offre.get("titre", "Offre d'emploi")

    exp_candidat = int(candidat.get("experience_annees", 0))
    exp_exigee   = int(offre.get("experience_min_annees", 0))

    comp_candidat_set = {c.lower() for c in candidat.get("competences", [])}
    comp_obligatoires  = offre.get("competences_obligatoires", [])

    motif_rejet = []

    # ── 1. Vérification de l'expérience minimale ──
    if exp_candidat < exp_exigee:
        diff = exp_exigee - exp_candidat
        motif_rejet.append(
            f"Expérience insuffisante : {exp_candidat} an(s) détruit(s) vs {exp_exigee} an(s) exigé(s) (manque {diff} an(s))."
        )

    # ── 2. Vérification des compétences obligatoires ──
    comp_manquantes = []
    for comp_req in comp_obligatoires:
        if comp_req.lower() not in comp_candidat_set:
            comp_manquantes.append(comp_req)

    # Si AUCUNE des compétences obligatoires n'est présente, rejet ferme
    if comp_obligatoires and len(comp_manquantes) == len(comp_obligatoires):
        motif_rejet.append(
            f"Aucune des compétences obligatoires présentes : manquantes ({', '.join(comp_manquantes)})."
        )

    # ── Résultat de l'évaluation ──
    if motif_rejet:
        raison = " | ".join(motif_rejet)
        logger.info(f"[HardFilter] REJETÉ — {nom_candidat} pour '{titre_offre}' : {raison}")
        return False, raison

    logger.info(f"[HardFilter] VALIDE — {nom_candidat} remplit les critères durs de '{titre_offre}'.")
    return True, "Critères durs validés avec succès."
