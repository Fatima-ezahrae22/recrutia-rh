"""
demo_test.py -- Demo complete sans chemin externe
Cree un vrai CV PDF et l'analyse avec traiter_cv()
"""
import sys, json, tempfile, os
sys.path.insert(0, ".")

import fitz
from ingestion.traiter_cv import traiter_cv

# === Creer un CV PDF de demo ===
tmpdir = tempfile.mkdtemp()
chemin_cv = os.path.join(tmpdir, "cv_demo_youssef.pdf")

doc = fitz.open()
page = doc.new_page()
contenu = """CURRICULUM VITAE

Nom       : Youssef AMRANI
Email     : youssef.amrani@email.ma
Tel       : +212 6 61 23 45 67
Ville     : Casablanca, Maroc

FORMATION
Ingenieur en Genie Informatique -- Ecole Mohammadia d'Ingenieurs (EMI), Rabat (2018-2023)
Baccalaureat Sciences Mathematiques -- Lycee Ibn Khaldoun (2018)

EXPERIENCE PROFESSIONNELLE

Developpeur Full Stack Python -- TechMaroc SARL (2023 - 2024)
  - Developpement d'une application web avec Django et React
  - Conception et gestion de bases de donnees PostgreSQL et MongoDB
  - Deploiement sur AWS avec Docker, CI/CD via GitHub Actions
  - Mise en place de REST API et architecture Microservices

Stagiaire Data Science -- DataVision Maroc (2022)
  - Machine Learning avec Scikit-learn, Pandas, NumPy
  - Visualisation de donnees avec Matplotlib et Seaborn
  - Traitement de langage naturel (NLP) avec spaCy

COMPETENCES TECHNIQUES
Langages    : Python, JavaScript, TypeScript, Java, C++
Frameworks  : Django, FastAPI, Flask, React, Node.js, Spring Boot
Bases       : PostgreSQL, MongoDB, MySQL, Redis, Elasticsearch
DevOps      : Docker, Kubernetes, GitHub Actions, AWS, Linux
IA/ML       : Machine Learning, Deep Learning, NLP, TensorFlow, PyTorch
Outils      : Git, Jira, Figma, Postman

LANGUES
Arabe (natif) | Francais (courant) | Anglais (professionnel)
"""
page.insert_text((50, 50), contenu, fontsize=10.5)
doc.save(chemin_cv)
doc.close()

# === Lancer le pipeline ===
print("\n" + "=" * 55)
print("  Agent IA RH -- Couche Ingestion | DEMO")
print("=" * 55)
print(f"  Fichier analyse : cv_demo_youssef.pdf\n")

resultat = traiter_cv(chemin_cv)

affichage = {
    "fichier"           : resultat["fichier"],
    "statut"            : resultat["statut"],
    "formation"         : resultat["formation"],
    "experience_annees" : resultat["experience_annees"],
    "competences"       : resultat["competences"],
    "message"           : resultat["message"],
    "duree_traitement"  : str(resultat["duree_traitement"]) + " s",
    "texte_brut_apercu" : resultat["texte_brut"][:250] + "..."
}

print("\nResultat JSON final :")
print(json.dumps(affichage, ensure_ascii=False, indent=2))
