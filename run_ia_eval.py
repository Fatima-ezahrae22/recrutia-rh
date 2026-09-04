# -*- coding: utf-8 -*-
"""
run_ia_eval.py — Démonstration complète de la Couche IA Agentique (Tâche 2)
Combines : CV ingéré (JSON Tâche 1) + Offre d'emploi -> Score + Justification
"""

import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, ".")

import logging
logging.disable(logging.CRITICAL)

from ingestion.traiter_cv import traiter_cv
from ia_agentic.evaluer_candidature import evaluer_candidature

DOSSIER_CV = "mes_cv"
FICHIER_OFFRES = os.path.join("data", "offres_exemples.json")

# Charger les offres exemples
with open(FICHIER_OFFRES, encoding="utf-8") as f:
    OFFRES = json.load(f)

# 1. Rechercher un CV réels dans mes_cv/
fichiers_cv = [
    f for f in os.listdir(DOSSIER_CV)
    if f.lower().endswith((".pdf", ".docx")) and not f.endswith("_resultat.json")
]

print()
print("╔══════════════════════════════════════════════════════════════════════╗")
print("║         AGENT IA RH  —  COUCHE 2 : IA AGENTIQUE & SCORING            ║")
print("╚══════════════════════════════════════════════════════════════════════╝")
print()

if not fichiers_cv:
    print("  ⚠️  Aucun CV trouvé dans mes_cv/. Veuillez y placer un CV.")
    sys.exit()

cv_choisi = os.path.join(DOSSIER_CV, fichiers_cv[0])
print(f"  📄 1. INGESTION DU CV : {fichiers_cv[0]}")
candidat_json = traiter_cv(cv_choisi)
print(f"     ✅ CV ingéré : {candidat_json['formation']} | Exp : {candidat_json['experience_annees']} an(s) | {len(candidat_json['competences'])} compétences.")
print()

print("  🎯 2. ÉVALUATION FACE AUX 3 OFFRES D'EMPLOI TYPES :")
print("  " + "─" * 68)

for clé_offre, offre in OFFRES.items():
    print(f"\n  📋 Offre : [{offre['id']}] {offre['titre']}")
    print(f"     Exigences : Exp min {offre['experience_min_annees']} an(s) | Requis : {', '.join(offre['competences_obligatoires'])}")

    # Appel de la fonction unique de la tâche 2
    res = evaluer_candidature(candidat_json, offre)

    print("     " + "─" * 50)
    if res["statut"] == "score":
        print(f"     ✅ SCORE DE CORRESPONDANCE : {res['score']} / 100")
        print(f"     ⏱️  Durée évaluation       : {res['duree_evaluation']} s")
        print("     📝 Justification RH        :")
        for line in res["justification"].splitlines():
            print(f"        {line}")
    else:
        print(f"     ❌ REJET AUTOMATIQUE CRITÈRES DURS (Score: 0.0 / 100)")
        print(f"     ⚠️  Motif du rejet : {res['details']['motif_rejet']}")
    print("     " + "─" * 50)

print("\n╔══════════════════════════════════════════════════════════════════════╗")
print("║  COUCHE IA AGENTIQUE VALIDÉE — PRÊTE POUR L'ORCHESTRATION BACKEND    ║")
print("╚══════════════════════════════════════════════════════════════════════╝\n")
