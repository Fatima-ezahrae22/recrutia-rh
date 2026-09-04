# Agent IA RH — Couche Ingestion

## Description
Module Python autonome qui transforme un CV brut (PDF ou DOCX) en dictionnaire structuré JSON.

## Installation

### 1. Installer les dépendances Python
```bash
pip install -r requirements.txt
python -m spacy download fr_core_news_md
```

### 2. Installer Tesseract OCR (Windows)
Télécharger et installer : https://github.com/UB-Mannheim/tesseract/wiki
→ Chemin par défaut : `C:\Program Files\Tesseract-OCR\tesseract.exe`
→ Ajouter les données langue : `fra.traineddata` (inclus dans l'installateur)

## Utilisation

```python
from ingestion.traiter_cv import traiter_cv

resultat = traiter_cv("cv_candidat.pdf")

print(resultat)
# {
#   "fichier":            "cv_candidat.pdf",
#   "competences":        ["Django", "Docker", "Python", "PostgreSQL"],
#   "experience_annees":  4,
#   "formation":          "Master / Ingénieur",
#   "texte_brut":         "...",
#   "statut":             "succès",
#   "message":            "CV traité avec succès (4 compétence(s) détectée(s)).",
#   "duree_traitement":   0.312
# }
```

## Lancer les tests

```bash
# Depuis la racine du projet
python -m pytest tests/test_ingestion.py -v

# Ou directement
python tests/test_ingestion.py
```

## Architecture

```
agent_ai/
├── ingestion/
│   ├── __init__.py        # Point d'entrée du package
│   ├── extractor.py       # Extraction PDF/DOCX/OCR
│   ├── cleaner.py         # Nettoyage et normalisation du texte
│   ├── parser.py          # Extraction compétences/expérience/formation
│   └── traiter_cv.py      # Orchestrateur principal
├── data/
│   └── competences_ref.json   # Liste de référence des compétences
├── tests/
│   └── test_ingestion.py  # Tests unitaires + intégration
└── requirements.txt
```

## Formats supportés
| Format | Méthode principale | Fallback |
|--------|-------------------|---------|
| PDF (texte natif) | pdfplumber | PyMuPDF |
| PDF (scanné/image) | PyMuPDF → OCR Tesseract | — |
| DOCX | python-docx | — |
