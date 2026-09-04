# -*- coding: utf-8 -*-
"""
previsualiser_dashboard.py — Test du chargement du Dashboard RH et remplissage d'exemples
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

print()
print("╔══════════════════════════════════════════════════════════════════════╗")
print("║         AGENT IA RH  —  INITIALISATION DU DASHBOARD RH (TÂCHE 4)     ║")
print("╚══════════════════════════════════════════════════════════════════════╝")
print()

# 1. Vérification chargement Dashboard HTML
res_dash = client.get("/dashboard")
print(f"  🌐 Statut route Dashboard (/dashboard) : {res_dash.status_code} OK")

# 2. Remplissage automatique de 3 offres d'emploi exemples pour la démo visuelle
offres_demo = [
    {
        "titre": "Développeur Senior Backend Python / Django",
        "description": "Poste de développement d'API REST performantes avec Python, Django, PostgreSQL et Docker.",
        "experience_min_annees": 3,
        "competences_obligatoires": ["Python", "Django"],
        "competences_souhaitees": ["Docker", "PostgreSQL", "REST API", "Git"]
    },
    {
        "titre": "Ingénieur Data Science & Machine Learning",
        "description": "Création de modèles ML/DL, NLP et Computer Vision avec TensorFlow et PyTorch.",
        "experience_min_annees": 1,
        "competences_obligatoires": ["Python", "Machine Learning"],
        "competences_souhaitees": ["TensorFlow", "PyTorch", "Scikit-learn", "NLP"]
    },
    {
        "titre": "Expert Cloud & DevOps Senior",
        "description": "Architecture infrastructure Kubernetes et AWS avec automatisation CI/CD.",
        "experience_min_annees": 5,
        "competences_obligatoires": ["Kubernetes", "AWS"],
        "competences_souhaitees": ["Docker", "CI/CD", "Linux"]
    }
]

for o in offres_demo:
    res = client.post("/api/offres", json=o)
    if res.status_code == 201:
        print(f"  ✅ Offre démo créée (ID #{res.json()['id']}) : {o['titre']}")

# 3. Soumission du CV réel MEKKI Fatima-Ezahrae
chemin_cv = os.path.join("mes_cv", "MEKKI_FATIMA-EZAHRAE_AI_Backend.pdf")
if os.path.exists(chemin_cv):
    with open(chemin_cv, "rb") as f:
        res_cand = client.post(
            "/api/candidatures",
            data={"offre_id": "2"},
            files={"fichier_cv": ("MEKKI_FATIMA-EZAHRAE_AI_Backend.pdf", f, "application/pdf")}
        )
    if res_cand.status_code == 201:
        cand = res_cand.json()
        print(f"  ✅ CV de Fatima-Ezahrae MEKKI analysé & scoré ({cand['score']}/100) pour l'offre Data Science !")

print()
print("╔══════════════════════════════════════════════════════════════════════╗")
print("║  ACCÈS AU DASHBOARD INTERACTIF RH :                                   ║")
print("║  👉 Ouvrez votre navigateur sur : http://127.0.0.1:8000              ║")
print("╚══════════════════════════════════════════════════════════════════════╝\n")
