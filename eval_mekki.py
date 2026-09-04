# -*- coding: utf-8 -*-
"""
eval_mekki.py — Évaluation IA Agentique du CV de Fatima-Ezahrae MEKKI
"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, ".")

import logging
logging.disable(logging.CRITICAL)

from ingestion.traiter_cv import traiter_cv
from ia_agentic.evaluer_candidature import evaluer_candidature

chemin_cv = os.path.join("mes_cv", "MEKKI_FATIMA-EZAHRAE_AI_Backend.pdf")
candidat = traiter_cv(chemin_cv)

with open(os.path.join("data", "offres_exemples.json"), encoding="utf-8") as f:
    offres = json.load(f)

print("\n" + "=" * 70)
print(f" ÉVALUATION DU CV : {candidat['fichier']}")
print(f" Profile : {candidat['formation']} | Exp : {candidat['experience_annees']} ans | {len(candidat['competences'])} compétences")
print("=" * 70)

for k, offre in offres.items():
    res = evaluer_candidature(candidat, offre)
    print(f"\n📌 OFFRE : {offre['titre']}")
    print(f"   STATUT : {res['statut'].upper()} | SCORE : {res['score']}/100")
    print(f"   JUSTIFICATION :\n{res['justification']}")
    print("-" * 70)
