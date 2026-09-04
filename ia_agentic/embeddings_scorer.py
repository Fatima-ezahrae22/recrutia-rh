"""
Module : embeddings_scorer.py
Rôle   : Étapes 2 & 3 de la Couche IA Agentique.
         Vectorise le profil candidat et l'offre d'emploi (Embeddings)
         et calcule un score sémantique et technique global sur 100.

Auteur : Agent IA RH — Couche IA Agentique
"""

import math
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Modèle d'embeddings par défaut
MODELE_EMBEDDINGS_DEFAUT = "all-MiniLM-L6-v2"
_model_cache = None


def _get_embedding_model():
    """Charge et met en cache le modèle d'embeddings sentence-transformers."""
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"[Embeddings] Chargement du modèle '{MODELE_EMBEDDINGS_DEFAUT}'...")
        _model_cache = SentenceTransformer(MODELE_EMBEDDINGS_DEFAUT)
        return _model_cache
    except Exception as e:
        logger.warning(f"[Embeddings] Impossible de charger sentence-transformers ({e}). Utilisation du fallback vectoriel.")
        return None


def _cosine_similarity(v1, v2) -> float:
    """Calcule la similarité cosinus entre deux vecteurs numériques."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def _vectoriser_texte_fallback(texte: str) -> Dict[str, float]:
    """Fallback TF-IDF léger en pur Python si sentence-transformers n'est pas chargé."""
    import re
    mots = re.findall(r"\w+", texte.lower())
    freq = {}
    for m in mots:
        if len(m) > 2:
            freq[m] = freq.get(m, 0) + 1
    total = sum(freq.values()) or 1
    return {k: v / total for k, v in freq.items()}


def _similarite_fallback(texte1: str, texte2: str) -> float:
    """Calcul de similarité par produit scalaire de fréquences de mots."""
    tf1 = _vectoriser_texte_fallback(texte1)
    tf2 = _vectoriser_texte_fallback(texte2)
    mots_communs = set(tf1.keys()).intersection(tf2.keys())
    if not mots_communs:
        return 0.0
    score = sum(tf1[m] * tf2[m] for m in mots_communs)
    norm1 = math.sqrt(sum(v * v for v in tf1.values()))
    norm2 = math.sqrt(sum(v * v for v in tf2.values()))
    return min(1.0, (score / (norm1 * norm2)) * 2.5) if (norm1 * norm2) > 0 else 0.0


def calculer_score_semantique(candidat: Dict[str, Any], offre: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    """
    Calcule le score de correspondance sémantique et technique global entre 0 et 100
    décomposé sur 4 sous-scores multi-critères :

    Pondération :
      - 40% : Score Compétences Techniques (Vectoriel + Mots-clés obligatoires)
      - 25% : Score Expérience Professionnelle (Années vs Exigences)
      - 20% : Score Soft Skills & Méthodologies (Agile, Git, Communication, Autonomie)
      - 15% : Score Formation & Langues (Diplôme vs Exigence, Trilinguisme)
    """
    # ── 1. Préparation des représentations textuelles ──
    competences_candidat = candidat.get("competences", [])
    exp_candidat = float(candidat.get("experience_annees", 0))
    formation_candidat = str(candidat.get("formation", ""))
    texte_cv = str(candidat.get("texte_brut", ""))

    texte_representation_candidat = (
        f"Formation: {formation_candidat}. "
        f"Expérience: {exp_candidat} ans. "
        f"Compétences: {', '.join(competences_candidat)}. "
        f"Aperçu: {texte_cv[:500]}"
    )

    comp_req = offre.get("competences_obligatoires", []) + offre.get("competences_souhaitees", [])
    texte_representation_offre = (
        f"Poste: {offre.get('titre', '')}. "
        f"Description: {offre.get('description', '')}. "
        f"Exigences: Expérience {offre.get('experience_min_annees', 0)} ans. "
        f"Compétences clés: {', '.join(comp_req)}."
    )

    # ── 2. Similarité vectorielle (Embeddings) ──
    model = _get_embedding_model()
    if model is not None:
        try:
            vec_cand = model.encode(texte_representation_candidat).tolist()
            vec_off  = model.encode(texte_representation_offre).tolist()
            score_vectoriel = max(0.0, min(1.0, _cosine_similarity(vec_cand, vec_off)))
        except Exception as e:
            logger.warning(f"[Embeddings] Erreur d'encodage : {e} -> fallback")
            score_vectoriel = _similarite_fallback(texte_representation_candidat, texte_representation_offre)
    else:
        score_vectoriel = _similarite_fallback(texte_representation_candidat, texte_representation_offre)

    # ── 3. Sous-Score 1 : Compétences Techniques (40%) ──
    from ingestion.parser import normaliser_competence

    comp_candidat_norm = {normaliser_competence(c).lower() for c in competences_candidat}
    comp_obligatoires = offre.get("competences_obligatoires", [])
    comp_souhaitees  = offre.get("competences_souhaitees", [])

    points_comp = 0.0
    total_points = 0.0
    presentes = []
    manquantes = []

    for c in comp_obligatoires:
        c_norm = normaliser_competence(c).lower()
        total_points += 2.0
        if c_norm in comp_candidat_norm or any(c_norm in cand_c for cand_c in comp_candidat_norm):
            points_comp += 2.0
            presentes.append(c)
        else:
            manquantes.append(c)

    for c in comp_souhaitees:
        c_norm = normaliser_competence(c).lower()
        total_points += 1.0
        if c_norm in comp_candidat_norm or any(c_norm in cand_c for cand_c in comp_candidat_norm):
            points_comp += 1.0
            if c not in presentes: presentes.append(c)
        else:
            if c not in manquantes: manquantes.append(c)

    ratio_mots_cles = (points_comp / total_points) if total_points > 0 else 0.6
    score_technique = round(((score_vectoriel * 0.5) + (ratio_mots_cles * 0.5)) * 100, 1)

    # ── 4. Sous-Score 2 : Expérience Professionnelle (25%) ──
    exp_req = float(offre.get("experience_min_annees", 0))
    if exp_req == 0:
        score_experience = 100.0
    else:
        ratio_exp = exp_candidat / exp_req
        score_experience = round(min(1.2, ratio_exp) / 1.2 * 100, 1)

    # ── 5. Sous-Score 3 : Soft Skills & Méthodologies (20%) ──
    soft_skills_mots = ["agile", "scrum", "git", "ci/cd", "autonomie", "rigueur", "equipe", "équipe", "communication", "résolution", "esprit d'équipe", "leadership"]
    cv_lower = texte_cv.lower()
    soft_matchs = sum(1 for kw in soft_skills_mots if kw in cv_lower or kw in comp_candidat_norm)
    score_soft_skills = round(min(100.0, 50.0 + (soft_matchs * 10.0)), 1)

    # ── 6. Sous-Score 4 : Formation & Langues (15%) ──
    formation_exigee = str(offre.get("formation_exigee", "")).lower()
    formation_cand_lower = formation_candidat.lower()
    score_form_base = 70.0
    if "ingénieur" in formation_cand_lower or "master" in formation_cand_lower or "doctorat" in formation_cand_lower:
        score_form_base = 95.0
    elif "licence" in formation_cand_lower or "bac+3" in formation_cand_lower:
        score_form_base = 80.0
    elif "dut" in formation_cand_lower or "bts" in formation_cand_lower or "bac+2" in formation_cand_lower:
        score_form_base = 75.0

    # Bonus langues (Arabe, Français, Anglais)
    bonus_langues = 0.0
    if "anglais" in cv_lower or "english" in cv_lower: bonus_langues += 5.0
    if "français" in cv_lower or "french" in cv_lower: bonus_langues += 5.0

    score_formation = round(min(100.0, score_form_base + bonus_langues), 1)

    # ── 7. Score Global Combiné (0 à 100) ──
    score_final_raw = (
        (score_technique * 0.40) +
        (score_experience * 0.25) +
        (score_soft_skills * 0.20) +
        (score_formation * 0.15)
    )
    score_final = round(score_final_raw, 1)

    seuil_min = float(offre.get("seuil_score_min", 70.0))
    recommande = score_final >= seuil_min

    details = {
        "score_technique": score_technique,
        "score_experience": score_experience,
        "score_soft_skills": score_soft_skills,
        "score_formation": score_formation,
        "score_vectoriel_pct": round(score_vectoriel * 100, 1),
        "score_competences_pct": round(ratio_mots_cles * 100, 1),
        "score_experience_pct": score_experience,
        "seuil_score_min": seuil_min,
        "recommande_par_ia": recommande,
        "competences_presentes": presentes,
        "competences_manquantes": manquantes,
        "conseils_ia": generer_conseils_candidat(score_final, exp_candidat, exp_req, presentes, manquantes)
    }

    logger.info(f"[EmbeddingsScorer] Score global: {score_final}/100 | Tech: {score_technique}% | Exp: {score_experience}% | Soft: {score_soft_skills}% | Form: {score_formation}%")
    return score_final, details


def generer_conseils_candidat(score: float, exp_cand: int, exp_req: int, presentes: list, manquantes: list) -> list:
    """Génère des retours et conseils personnalisés pour aider le candidat à valoriser son profil."""
    conseils = []
    if score >= 75:
        conseils.append("🌟 Profil très pertinent ! Vos compétences clés correspondent aux besoins prioritaires de l'offre.")
    elif score >= 50:
        conseils.append("💡 Bon potentiel global. Quelques compétences complémentaires pourraient renforcer votre profil.")
    else:
        conseils.append("📌 Profil nécessitant un renforcement sur les exigences clés du poste.")

    if exp_cand < exp_req:
        conseils.append(f"⏱️ Expérience : L'offre demande {exp_req} an(s). Mettez en avant vos projets pratiques et réalisations concrètes.")

    if manquantes:
        mots_manquants = ", ".join(manquantes[:3])
        conseils.append(f"🎯 Mots-clés suggérés pour votre CV : Pensez à préciser votre niveau sur ({mots_manquants}) si vous les avez déjà pratiqués.")

    if presentes:
        conseils.append(f"✅ Atouts majeurs détectés : {', '.join(presentes[:4])}.")

    return conseils
