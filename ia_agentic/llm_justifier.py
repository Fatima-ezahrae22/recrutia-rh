"""
Module : llm_justifier.py
Rôle   : Étape 4 de la Couche IA Agentique.
         Génère une justification argumentée, claire et traçable du score
         en utilisant Groq API, Ollama local ou le moteur déterministe anti-hallucination.

Auteur : Agent IA RH — Couche IA Agentique
"""

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def _justification_deterministe(
    candidat: Dict[str, Any],
    offre: Dict[str, Any],
    score: float,
    details: Dict[str, Any]
) -> str:
    """
    Génère une justification 100% fiable et traçable basée STRICTEMENT sur les données extraites.
    Sert de garde-fou absolu anti-hallucination.
    """
    nom_cand = candidat.get("fichier", "Candidat Anonyme")
    titre_offre = offre.get("titre", "l'offre d'emploi")

    formation = candidat.get("formation", "Non spécifié")
    exp_cand = candidat.get("experience_annees", 0)
    exp_req  = offre.get("experience_min_annees", 0)

    comp_presentes = details.get("competences_presentes", [])
    comp_manquantes = details.get("competences_manquantes", [])

    st = details.get("score_technique", 0.0)
    se = details.get("score_experience", 0.0)
    ss = details.get("score_soft_skills", 0.0)
    sf = details.get("score_formation", 0.0)
    seuil = details.get("seuil_score_min", 70.0)

    points_forts = []
    points_faibles = []

    # Analyse formation
    if formation != "Non spécifié":
        points_forts.append(f"Formation académique validée ({formation}).")

    # Analyse expérience
    if exp_cand >= exp_req:
        points_forts.append(f"Niveau d'expérience conforme aux exigences ({exp_cand} an(s) d'expérience pour {exp_req} an(s) requis).")
    else:
        points_faibles.append(f"Expérience inférieure au seuil idéal ({exp_cand} an(s) vs {exp_req} an(s) souhaités).")

    # Analyse compétences
    if comp_presentes:
        points_forts.append(f"Compétences clés maîtrisées : {', '.join(comp_presentes)}.")
    if comp_manquantes:
        points_faibles.append(f"Compétences non détectées dans le CV : {', '.join(comp_manquantes)}.")

    # Synthèse globale
    if score >= seuil:
        appreciation = f"RECOMMANDÉ (Score {score}% >= Seuil {seuil}%). Profil réactif et conforme aux besoins du poste."
    else:
        appreciation = f"NON RECOMMANDÉ (Score {score}% < Seuil {seuil}%). Profil nécessitant un renforcement technique ou d'expérience."

    lignes = [
        f"📋 ÉVALUATION MULTI-CRITÈRES DU CANDIDAT ({nom_cand}) — POSTE : '{titre_offre}'",
        f"🎯 Score Global : {score}/100 | Seuil Minimal d'Adéquation : {seuil}%",
        f"📊 Décomposition : Technique {st}% | Expérience {se}% | Soft Skills {ss}% | Formation {sf}%",
        "",
        f" Appréciation IA : {appreciation}",
        "",
        " Points Forts Détectés :",
        "\n".join(f"  • {p}" for p in points_forts) if points_forts else "  • Aucun point fort particulier.",
        "",
        " Axes d'Amélioration / Écarts :",
        "\n".join(f"  • {p}" for p in points_faibles) if points_faibles else "  • Aucun écart critique identifié.",
        "",
        " 🛡️ Audit d'Impartialité : Évaluation basée exclusivement sur les compétences et l'expérience. Exclusions garanties : genre, âge, origine et apparence."
    ]

    return "\n".join(lignes)


def _appeler_groq_api(prompt: str) -> str:
    """Tente un appel à l'API Groq si la clé GROQ_API_KEY est présente."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return ""

    try:
        import requests
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_FEW_SHOT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=10)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning(f"[LLMJustifier] Échec Groq API : {e}")
    return ""


def _appeler_ollama_local(prompt: str) -> str:
    """Tente un appel à Ollama en local (http://localhost:11434)."""
    try:
        import requests
        data = {
            "model": "llama3",
            "prompt": f"{SYSTEM_PROMPT_FEW_SHOT}\n\n{prompt}",
            "stream": False
        }
        resp = requests.post("http://localhost:11434/api/generate", json=data, timeout=5)
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
    except Exception:
        pass
    return ""


# ── FEW-SHOT PROMPT SYSTEM WITH 3 CALIBRATION EXAMPLES ──
SYSTEM_PROMPT_FEW_SHOT = """Tu es un expert RH impartial et bienveillant spécialisé dans l'évaluation éthique des recrutements.
Tu rédiges des explications de scoring précises et traçables en analysant la décomposition multi-critères :
1. Score Compétences Techniques (40%)
2. Score Expérience Professionnelle (25%)
3. Score Soft Skills & Méthodologies (20%)
4. Score Formation & Langues (15%)

Voici 3 exemples de référence (Few-Shot Calibration) à suivre :

--- EXEMPLE 1 : PROFIL EXCELLENT (Score >= 90%) ---
CANDIDAT: Youssef Amrani, 4 ans exp, React, Python, FastAPI, Docker, PostgreSQL, Master Ingénieur
OFFRE: Développeur Full Stack React/Python (3 ans exp min)
SCORES: Global 93.5% (Tech: 95%, Exp: 100%, Soft: 90%, Form: 95%) | Seuil: 70%
JUSTIFICATION EXEMPLE:
"Excellent profil (93.5/100) dépassant largement le seuil requis de 70%. Le candidat possède 4 ans d'expérience vs 3 ans exigés et maîtrise l'ensemble de la stack (React, Python, FastAPI, Docker). Les compétences méthodologiques et la solide formation d'ingénieur garantissent une intégration immédiate."

--- EXEMPLE 2 : PROFIL INTERMÉDIAIRE (Score 60-75%) ---
CANDIDAT: Amina Bennani, 1.5 ans exp, Python, Flask, HTML/CSS, Licence Informatique
OFFRE: Développeur Senior Backend Python (3 ans exp min, FastAPI, Docker)
SCORES: Global 64.0% (Tech: 65%, Exp: 50%, Soft: 70%, Form: 80%) | Seuil: 70%
JUSTIFICATION EXEMPLE:
"Profil intermédiaire (64.0/100) en-deçà du seuil recommandé de 70%. Bien que possédant de bonnes bases en Python et Flask, l'expérience professionnelle (1.5 an vs 3 ans exigés) et l'absence de pratique démontrée sur FastAPI et Docker nécessiteront un accompagnement technique."

--- EXEMPLE 3 : PROFIL INADÉQUAT (Score < 40%) ---
CANDIDAT: Omar Tazi, 0.5 an exp, Excel, Word, Support Client, BTS Gestion
OFFRE: Data Scientist / Intelligence Artificielle (Python, TensorFlow, NLP, Scikit-Learn)
SCORES: Global 32.5% (Tech: 20%, Exp: 25%, Soft: 50%, Form: 55%) | Seuil: 70%
JUSTIFICATION EXEMPLE:
"Profil non retenu (32.5/100) très éloigné du seuil de 70%. Aucune compétence en programmation Python, Deep Learning ou NLP n'est identifiée. Le parcours est orienté support bureautique, sans adéquation avec les exigences scientifiques et techniques du poste."

RÈGLE ABSOLUE : Utilise les 4 sous-scores fournis dans le prompt utilisateur pour rédiger la justification finale en 3 à 5 phrases sans rien inventer.
"""


def generer_justification(
    candidat: Dict[str, Any],
    offre: Dict[str, Any],
    score: float,
    details: Dict[str, Any]
) -> str:
    """
    Génère la justification argumentée du score.
    Cascade de génération : Groq API ➔ Ollama ➔ Moteur Déterministe Anti-Hallucination.
    """
    st = details.get("score_technique", score)
    se = details.get("score_experience", score)
    ss = details.get("score_soft_skills", score)
    sf = details.get("score_formation", score)
    seuil = details.get("seuil_score_min", 70.0)

    prompt = f"""
Voici les données du candidat et de l'offre d'emploi :

CANDIDAT:
- Nom/Fichier: {candidat.get('fichier', 'Candidat')}
- Formation: {candidat.get('formation', 'Inconnue')}
- Expérience: {candidat.get('experience_annees', 0)} ans
- Compétences extraites: {', '.join(candidat.get('competences', []))}

OFFRE D'EMPLOI:
- Titre: {offre.get('titre', '')}
- Expérience exigée: {offre.get('experience_min_annees', 0)} ans
- Compétences recherchées: {', '.join(offre.get('competences_obligatoires', []) + offre.get('competences_souhaitees', []))}
- Seuil minimum d'adéquation: {seuil}%

SCORES MULTI-CRITÈRES CALCULÉS:
- Score Global: {score}/100
- Score Technique (40%): {st}%
- Score Expérience (25%): {se}%
- Score Soft Skills (20%): {ss}%
- Score Formation & Langues (15%): {sf}%

Compétences présentement validées: {', '.join(details.get('competences_presentes', []))}
Compétences manquantes: {', '.join(details.get('competences_manquantes', []))}

Consigne : Rédige une justification synthétique RH claire en te basant exactement sur les exemples de référence.
"""

    # 1. Groq API
    reponse_llm = _appeler_groq_api(prompt)
    if reponse_llm:
        logger.info("[LLMJustifier] Justification générée via Groq API (Few-Shot) ✓")
        return reponse_llm

    # 2. Ollama Local
    reponse_llm = _appeler_ollama_local(prompt)
    if reponse_llm:
        logger.info("[LLMJustifier] Justification générée via Ollama local (Few-Shot) ✓")
        return reponse_llm

    # 3. Fallback Déterministe
    logger.info("[LLMJustifier] Génération via le moteur déterministe anti-hallucination ✓")
    return _justification_deterministe(candidat, offre, score, details)
