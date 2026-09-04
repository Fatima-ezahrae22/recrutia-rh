# -*- coding: utf-8 -*-
"""
run.py — Lance le projet et affiche le resultat proprement
Commande : python run.py
"""

import sys, os, json, tempfile
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, ".")

# ── Imports du projet ──
from ingestion.traiter_cv import traiter_cv
import fitz  # PyMuPDF

# ─────────────────────────────────────────────────────────
# ETAPE 0 : Créer un CV PDF de démonstration
# ─────────────────────────────────────────────────────────
tmpdir    = tempfile.mkdtemp()
chemin_cv = os.path.join(tmpdir, "cv_youssef_amrani.pdf")

doc  = fitz.open()
page = doc.new_page()
cv_texte = """\
CURRICULUM VITAE
-------------------------------------------------
Nom    : Youssef AMRANI
Email  : youssef.amrani@email.ma
Tel    : +212 6 61 23 45 67
Ville  : Casablanca, Maroc
-------------------------------------------------

FORMATION
Ingénieur en Génie Informatique
École Mohammadia d'Ingénieurs (EMI), Rabat
2018 - 2023

Baccalauréat Sciences Mathématiques
Lycée Ibn Khaldoun, Casablanca — 2018

-------------------------------------------------
EXPÉRIENCE PROFESSIONNELLE

Développeur Full Stack — TechMaroc SARL (2023 - 2024)
  Développement web avec Django et React
  Bases de données : PostgreSQL, MongoDB
  Déploiement : AWS, Docker, GitHub Actions, CI/CD

Stagiaire Data Science — DataVision Maroc (2022)
  Machine Learning avec Scikit-learn, Pandas, NumPy
  Deep Learning avec TensorFlow et PyTorch
  Traitement NLP avec spaCy

-------------------------------------------------
COMPÉTENCES TECHNIQUES
Langages    : Python, JavaScript, TypeScript, Java, C++
Frameworks  : Django, FastAPI, Flask, React, Node.js
Bases       : PostgreSQL, MongoDB, MySQL, Redis
DevOps      : Docker, Kubernetes, GitHub Actions, AWS, Linux
IA/ML       : Machine Learning, Deep Learning, NLP, TensorFlow, PyTorch
Outils      : Git, Jira, Figma

LANGUES
Arabe (natif) | Français (courant) | Anglais (professionnel)
"""
page.insert_text((50, 50), cv_texte, fontsize=10)
doc.save(chemin_cv)
doc.close()

# ─────────────────────────────────────────────────────────
# ETAPE 1 : Lancer le pipeline traiter_cv()
# ─────────────────────────────────────────────────────────
import logging
logging.disable(logging.CRITICAL)   # masquer les logs techniques

print()
print("╔══════════════════════════════════════════════════════╗")
print("║        AGENT IA RH — Couche Ingestion               ║")
print("║        Analyse automatique d'un CV                  ║")
print("╚══════════════════════════════════════════════════════╝")
print()
print(f"  📄 Fichier CV : cv_youssef_amrani.pdf")
print(f"  ⏳ Traitement en cours...")
print()

resultat = traiter_cv(chemin_cv)

# ─────────────────────────────────────────────────────────
# ETAPE 2 : Affichage propre du résultat
# ─────────────────────────────────────────────────────────

print("╔══════════════════════════════════════════════════════╗")
print("║                  RÉSULTAT FINAL                     ║")
print("╚══════════════════════════════════════════════════════╝")
print()

statut_icone = "✅" if resultat["statut"] == "succès" else "❌"
print(f"  {statut_icone}  Statut          : {resultat['statut'].upper()}")
print(f"  🎓  Formation        : {resultat['formation']}")
print(f"  📅  Expérience       : {resultat['experience_annees']} an(s)")
print(f"  ⏱️   Durée traitement : {resultat['duree_traitement']} s")
print()

print("  🛠️  Compétences détectées :")
comps = resultat["competences"]
# Afficher 4 par ligne
for i in range(0, len(comps), 4):
    ligne = comps[i:i+4]
    print("      " + "  |  ".join(f"{c:<18}" for c in ligne))

print()
print("  📝  Aperçu du texte extrait et nettoyé :")
print("  " + "─" * 52)
apercu = resultat["texte_brut"][:350].replace("\n", "\n  ")
print(f"  {apercu}...")
print("  " + "─" * 52)
print()
print("  📦  Résultat JSON complet :")
print()

# JSON final (sans texte brut pour lisibilité)
json_final = {
    "fichier"           : resultat["fichier"],
    "statut"            : resultat["statut"],
    "formation"         : resultat["formation"],
    "experience_annees" : resultat["experience_annees"],
    "nb_competences"    : len(resultat["competences"]),
    "competences"       : resultat["competences"],
    "message"           : resultat["message"],
    "duree_traitement"  : str(resultat["duree_traitement"]) + " s",
}
print(json.dumps(json_final, ensure_ascii=False, indent=4))
print()
print("══════════════════════════════════════════════════════")
print("  Couche Ingestion terminée — Prête pour la couche IA")
print("══════════════════════════════════════════════════════")
print()
