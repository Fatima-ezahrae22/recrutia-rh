# -*- coding: utf-8 -*-
"""
demo_backend.py — Démonstration visuelle de la Tâche 3 (Backend API & Pipeline)
"""

import sys, os, time, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

print()
print("╔══════════════════════════════════════════════════════════════════════╗")
print("║     AGENT IA RH — DÉMONSTRATION FLUX BACKEND END-TO-END (TÂCHE 3)    ║")
print("╚══════════════════════════════════════════════════════════════════════╝")
print()

# ── 1. Création d'une offre d'emploi RH ──
print(" 📝 1. CRÉATION D'UNE OFFRE D'EMPLOI PAR LE RECRUTEUR RH...")
offre_payload = {
    "titre": "Ingénieur Data Science & Machine Learning",
    "description": "Nous recherchons un ingénieur IA pour créer des modèles NLP et Computer Vision.",
    "experience_min_annees": 1,
    "competences_obligatoires": ["Python", "Machine Learning"],
    "competences_souhaitees": ["TensorFlow", "Scikit-learn", "NLP", "PyTorch"],
    "formation_exigee": "Master / Ingénieur"
}
res_offre = client.post("/api/offres", json=offre_payload)
offre = res_offre.json()
print(f"    ✅ Offre créée en BDD (ID #{offre['id']}) : '{offre['titre']}'")
print(f"       Exigences : {offre['experience_min_annees']} an(s) exp | Requis : {', '.join(offre['competences_obligatoires'])}")
print()

# ── 2. Soumission d'un vrai CV réels (MEKKI Fatima-Ezahrae) ──
chemin_cv = os.path.join("mes_cv", "MEKKI_FATIMA-EZAHRAE_AI_Backend.pdf")
if not os.path.exists(chemin_cv):
    # Si non présent, prendre le premier disponible
    fichiers = [f for f in os.listdir("mes_cv") if f.endswith(".pdf")]
    chemin_cv = os.path.join("mes_cv", fichiers[0])

nom_fichier = os.path.basename(chemin_cv)
print(f" 📄 2. SOUMISSION DU CV AU BACKEND : '{nom_fichier}'...")
print("    ⏳ Exécution du pipeline (Ingestion Tâche 1 ➔ Scoring Tâche 2 ➔ Sauvegarde DB)...")

with open(chemin_cv, "rb") as f:
    res_cand = client.post(
        "/api/candidatures",
        data={"offre_id": str(offre["id"])},
        files={"fichier_cv": (nom_fichier, f, "application/pdf")}
    )

cand = res_cand.json()
print(f"    ✅ Candidature enregistrée en BDD (ID #{cand['id']}) en {cand['duree_traitement_sec']}s !")
print()

# ── 3. Affichage du Résultat de l'Évaluation ──
print("╔══════════════════════════════════════════════════════════════════════╗")
print("║               RÉSULTAT DE L'ANALYSE & DU SCORING BDD                 ║")
print("╚══════════════════════════════════════════════════════════════════════╝")
print(f"  👤 Candidat Extrait   : {cand['candidat']['nom']} ({cand['candidat']['email'] or 'email non spécifié'})")
print(f"  📊 Statut IA          : {cand['statut_ia'].upper()}")
print(f"  ⭐️ Score de Matching  : {cand['score']} / 100")
print(f"  📋 Statut Décision RH : {cand['decision_rh']}")
print()
print("  📝 Justification Générée :")
print("  " + "─" * 60)
for line in cand["justification_ia"].splitlines():
    print(f"     {line}")
print("  " + "─" * 60)
print()

# ── 4. Prise de décision par le RH ──
print(" ⚖️ 4. ENREGISTREMENT DE LA DÉCISION DU RECRUTEUR RH...")
decision_payload = {
    "decision": "VALIDE",
    "note_rh": "Profil très prometteur validé par le recruteur. Entretien planifié.",
    "rh_utilisateur": "Responsable RH ArtiWeb"
}
res_dec = client.patch(f"/api/candidatures/{cand['id']}/decision", json=decision_payload)
cand_updated = res_dec.json()
print(f"    ✅ Décision enregistrée : {cand_updated['decision_rh']} par {cand_updated['rh_utilisateur']}")
print(f"       Note RH : \"{cand_updated['note_rh']}\"")
print()

# ── 5. Consultation de l'historique d'audit ──
print(" 📜 5. CONSULTATION DE LA TRAÇABILITÉ D'AUDIT (GET /api/audit)...")
res_audit = client.get("/api/audit")
logs = res_audit.json()
for log in logs[:3]:
    print(f"    • [{log['timestamp'][:19]}] {log['action']} : {log['details']}")

print()
print("╔══════════════════════════════════════════════════════════════════════╗")
print("║  FLUX BACKEND END-TO-END VALIDÉ — PRÊT POUR L'INTERFACE DASHBOARD    ║")
print("╚══════════════════════════════════════════════════════════════════════╝\n")
