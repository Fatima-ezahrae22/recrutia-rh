# -*- coding: utf-8 -*-
"""
generer_pdf_complet.py
Génère un PDF ultra-détaillé expliquant le fonctionnement, les tests et l'architecture.
"""
import sys, os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

pdf_filename = "Rapport_de_Stage_Complet_Architecture_Tests.pdf"
doc = SimpleDocTemplate(
    pdf_filename,
    pagesize=letter,
    rightMargin=36,
    leftMargin=36,
    topMargin=36,
    bottomMargin=36
)

styles = getSampleStyleSheet()

# Colors
C_PRIMARY = colors.HexColor('#003366')    # Navy
C_SECONDARY = colors.HexColor('#0066CC')  # Blue
C_TEXT = colors.HexColor('#222222')
C_BG_CODE = colors.HexColor('#F8F9FA')

# Custom Styles
title_style = ParagraphStyle(
    'DocTitle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=18,
    leading=22,
    textColor=C_PRIMARY,
    alignment=1,
    spaceAfter=8
)

subtitle_style = ParagraphStyle(
    'DocSubtitle',
    parent=styles['Normal'],
    fontName='Helvetica-Oblique',
    fontSize=10,
    leading=13,
    textColor=C_SECONDARY,
    alignment=1,
    spaceAfter=15
)

h1_style = ParagraphStyle(
    'H1',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=13,
    leading=16,
    textColor=C_PRIMARY,
    spaceBefore=14,
    spaceAfter=6
)

h2_style = ParagraphStyle(
    'H2',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=11,
    leading=14,
    textColor=C_SECONDARY,
    spaceBefore=10,
    spaceAfter=4
)

body_style = ParagraphStyle(
    'Body',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=9,
    leading=12.5,
    textColor=C_TEXT,
    spaceAfter=5
)

bullet_style = ParagraphStyle(
    'Bullet',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=9,
    leading=12.5,
    textColor=C_TEXT,
    leftIndent=12,
    spaceAfter=3
)

code_style = ParagraphStyle(
    'Code',
    parent=styles['Normal'],
    fontName='Courier',
    fontSize=7.5,
    leading=9.5,
    textColor=colors.HexColor('#111111'),
    backColor=C_BG_CODE,
    borderColor=colors.HexColor('#DDDDDD'),
    borderWidth=0.5,
    borderPadding=5,
    spaceBefore=4,
    spaceAfter=6
)

story = []

# Title Header
story.append(Paragraph("RAPPORT DE STAGE ET DOCUMENTATION TECHNIQUE DÉTAILLÉE", title_style))
story.append(Paragraph("<b>Projet :</b> Agent IA RH (RecrutIA) — Module 1 : Ingestion Intelligente de CV<br/><b>Entreprise d'Accueil :</b> ARTIWEB (Fès, Maroc — Partenaire Google)", subtitle_style))
story.append(HRFlowable(width="100%", thickness=1.5, color=C_PRIMARY, spaceAfter=12))

# SECTION I
story.append(Paragraph("I. PRESENTATION DE L'ENTREPRISE ARTIWEB & FICHE PROJET", h1_style))
story.append(Paragraph("<b>ArtiWeb</b> est une agence de communication et marketing digital basée à Fès (https://artiweb.ma/). Partenaire Google certifié, elle propose des expertises en stratégie digitale, développement web/mobile, SEO/SEM, Social Ads et solutions E-commerce/Marketplace. Contacts : contact@artiweb.ma | (+212) 664-017447.", body_style))
story.append(Paragraph("<b>Problématique du projet RecrutIA :</b> Le tri manuel des candidatures par les RH est long, coûteux, sujet à la fatigue et aux biais. <i>L'objectif est d'automatiser l'analyse et la pré-sélection des CV grâce à un système intelligent à 3 couches (Ingestion ➔ IA Agentique ➔ Supervision Humaine).</i>", body_style))

# SECTION II
story.append(Paragraph("II. ARCHITECTURE TECHNIQUE DU MODULE D'INGESTION", h1_style))
story.append(Paragraph("La <b>Couche d'Ingestion</b> a été construite sous la forme d'un package Python modulaire et indépendant (développé dans <code>agent_ai/ingestion/</code>) :", body_style))

tree_str = """agent_ai/
├── ingestion/
│   ├── __init__.py        # Export officiel de la fonction traiter_cv()
│   ├── extractor.py       # Algorithme d'extraction cascade (PDF / DOCX / OCR Tesseract)
│   ├── cleaner.py         # Nettoyage, normalisation Unicode NFC, suppression du bruit
│   ├── parser.py          # Parsing NLP : compétences, durées d'expérience, diplômes
│   └── traiter_cv.py      # Orchestrateur central du pipeline de traitement
├── data/
│   └── competences_ref.json # Dictionnaire JSON de référence (~80 compétences)
├── mes_cv/                # Repertoire de test pour les CV réels
├── tests/
│   └── test_ingestion.py  # Suite complète de 21 tests unitaires et d'intégration
├── run.py / demo_test.py  # Scripts de démonstration exécutables
└── requirements.txt       # Dépendances (pdfplumber, PyMuPDF, python-docx, pytesseract, Pillow)"""

story.append(Paragraph(tree_str.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))

# SECTION III
story.append(Paragraph("III. MÉTHODE DE FONCTIONNEMENT DÉTAILLÉE (LE PIPELINE)", h1_style))
story.append(Paragraph("Le traitement d'un CV se déroule selon un pipeline strict en 4 étapes orchestré par <code>traiter_cv.py</code> :", body_style))

story.append(Paragraph("Étape 1 : Extraction du Texte en Cascade (extractor.py)", h2_style))
story.append(Paragraph("Pour garantir de lire 100% des fichiers reçus, l'extracteur applique une stratégie d'escalade :", body_style))
story.append(Paragraph("• <b>Fichiers .DOCX (Word) :</b> Utilisation de <code>python-docx</code> pour parcourir tous les paragraphes et les cellules de tableaux.", bullet_style))
story.append(Paragraph("• <b>Fichiers .PDF Textuels (Niveau 1) :</b> Utilisation de <code>pdfplumber</code> qui extrait le texte natif tout en conservant la disposition.", bullet_style))
story.append(Paragraph("• <b>Fichiers .PDF Complexes (Niveau 2) :</b> Si pdfplumber donne peu de texte, recours immédiat à <code>PyMuPDF (fitz)</code>.", bullet_style))
story.append(Paragraph("• <b>Fichiers .PDF Scannés / Images (Niveau 3 - Fallback OCR) :</b> Si le texte extrait fait &lt; 80 caractères, PyMuPDF convertit chaque page en une image HD (300 DPI) et <code>pytesseract</code> (moteur OCR Tesseract) analyse les pixels pour restituer le texte.", bullet_style))

story.append(Paragraph("Étape 2 : Nettoyage & Normalisation (cleaner.py)", h2_style))
story.append(Paragraph("Le texte extrait brut contient souvent du bruit. Le nettoyeur applique les corrections suivantes :", body_style))
story.append(Paragraph("• <b>Normalisation Unicode NFC :</b> Standardisation des encodages et conversion des ligatures PDF (ex: 'ﬁ' ➔ 'fi').", bullet_style))
story.append(Paragraph("• <b>Suppression du bruit visuel :</b> Élimination des symboles graphiques (•, ★, ▪, ✓) via Regex.", bullet_style))
story.append(Paragraph("• <b>Correction des mots coupés :</b> Fusion des mots scindés par un tiret en fin de ligne (ex: 'Déve-\\nloppeur' ➔ 'Développeur').", bullet_style))
story.append(Paragraph("• <b>Suppression des en-têtes/pieds de page :</b> Élimination des mentions répétitives type 'Page 1 sur 2'.", bullet_style))

story.append(Paragraph("Étape 3 : Parsing & Extraction NLP d'Informations (parser.py)", h2_style))
story.append(Paragraph("Le texte propre est analysé pour extraire 3 entités clés :", body_style))
story.append(Paragraph("• <b>1. Compétences :</b> Comparaison insensible à la casse avec le fichier <code>competences_ref.json</code>. Scan d'abord dans les sections dédiées ('Compétences', 'Stack', 'Outillage') puis scan global.", bullet_style))
story.append(Paragraph("• <b>2. Expérience (Années) :</b> Repérage des mentions explicites ('X ans d'expérience') via Regex. En l'absence de mention explicite, extraction de toutes les plages d'années (ex: 2019-2023), fusion des périodes chevauchantes et calcul du cumul réel d'années.", bullet_style))
story.append(Paragraph("• <b>3. Formation :</b> Application d'une hiérarchie stricte (Doctorat/PhD &gt; Master/Ingénieur &gt; Licence/Bachelor &gt; BTS/DUT &gt; Bac). La fonction renvoie le niveau le plus élevé détecté.", bullet_style))

story.append(Paragraph("Étape 4 : Assemblage du Résultat JSON (traiter_cv.py)", h2_style))
story.append(Paragraph("Le pipeline assemble les données extraites et mesure la durée d'exécution. Il génère un dictionnaire structuré au format JSON prêt pour l'IA.", body_style))

# SECTION IV
story.append(Paragraph("IV. EXPLICATION DÉTAILLÉE DES TESTS AUTOMATISÉS (21 TESTS)", h1_style))
story.append(Paragraph("Le fichier <code>tests/test_ingestion.py</code> contient <b>21 tests automatiques</b> exécutés via <code>pytest</code> :", body_style))

story.append(Paragraph("1. Suite Unitaires Nettoyeur (TestCleaner - 5 tests)", h2_style))
story.append(Paragraph("• <code>test_suppression_caracteres_parasites</code> : Vérifie le retrait des symboles (•, ★).", bullet_style))
story.append(Paragraph("• <code>test_ligatures_pdf</code> : Vérifie la conversion de 'ﬁ' en 'fi'.", bullet_style))
story.append(Paragraph("• <code>test_normalisation_unicode</code> & <code>test_espaces_multiples</code> : Vérifie la propreté du texte.", bullet_style))

story.append(Paragraph("2. Suite Unitaires Parseur (TestParser - 9 tests)", h2_style))
story.append(Paragraph("• <code>test_extraction_competences_basique</code> & <code>_insensible_casse</code> : Vérifie le matching de compétences.", bullet_style))
story.append(Paragraph("• <code>test_experience_mention_explicite</code> & <code>_calcul_dates</code> : Vérifie la détection directe '5 ans' et le calcul automatique à partir de dates chevauchantes.", bullet_style))
story.append(Paragraph("• <code>test_formation_priorite_plus_haut_niveau</code> : Envoie un texte avec 'Bac' + 'Master' + 'PhD' et vérifie que la réponse est bien 'Doctorat / PhD'.", bullet_style))

story.append(Paragraph("3. Suite d'Intégration Pipeline (TestIntegrationTraiterCV - 7 tests)", h2_style))
story.append(Paragraph("Ces tests créent de <b>vrais fichiers virtuels PDF et DOCX temporaires sur le disque</b> et les font passer par tout le pipeline :", body_style))
story.append(Paragraph("• <code>test_cv_pdf_bien_formate</code> : PDF natif ➔ Valide le succès et l'extraction complète.", bullet_style))
story.append(Paragraph("• <code>test_cv_pdf_mal_formate</code> : PDF avec symboles et bruit ➔ Valide la robustesse du nettoyeur.", bullet_style))
story.append(Paragraph("• <code>test_cv_docx</code> : Document Word avec tableaux ➔ Valide l'extraction python-docx.", bullet_style))
story.append(Paragraph("• <code>test_fichier_inexistant</code> & <code>_format_non_supporte</code> : Valide la gestion d'erreurs propre sans crash.", bullet_style))

story.append(Paragraph("<b>Résultat de la suite de tests : 21/21 PASSED (100% de réussite en 0.91 seconde).</b>", body_style))

# SECTION V
story.append(Paragraph("V. VALIDATION SUR LE CV RÉEL (MEKKI_FATIMA-EZAHRAE_AI_Backend.pdf)", h1_style))
story.append(Paragraph("Testé en conditions réelles avec le script <code>analyser_mon_cv.py</code> :", body_style))
story.append(Paragraph("• <b>Fichier :</b> MEKKI_FATIMA-EZAHRAE_AI_Backend.pdf | <b>Statut :</b> SUCCÈS", bullet_style))
story.append(Paragraph("• <b>Formation :</b> Master / Ingénieur (Détecté 'Ingénieure en Génie Informatique')", bullet_style))
story.append(Paragraph("• <b>Expérience :</b> 2 an(s) | <b>Durée de traitement :</b> 0.782 seconde", bullet_style))
story.append(Paragraph("• <b>33 Compétences extraites :</b> Python, Django, Flask, TensorFlow, React, Azure, Java, MySQL, Node.js, Scikit-learn, REST API, etc.", bullet_style))

json_real = """{
    "fichier": "MEKKI_FATIMA-EZAHRAE_AI_Backend.pdf",
    "statut": "succès",
    "formation": "Master / Ingénieur",
    "experience_annees": 2,
    "nb_competences": 33,
    "competences": ["Azure", "Bootstrap", "CSS", "Cloud", "Computer Vision", "Django", "Flask", "Python", "React", ...],
    "duree_traitement": "0.782 s"
}"""
story.append(Paragraph(json_real.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))

# SECTION VI
story.append(Paragraph("VI. CONCLUSION", h1_style))
story.append(Paragraph("Le module d'ingestion développé pour <b>ArtiWeb</b> est complet, modulaire, ultra-rapide (&lt; 1s) et totalement autonome. Il fournit le contrat de données JSON nécessaire à la future Couche d'IA Agentique (Couche 2).", body_style))

doc.build(story)
print(f"PDF détaillé généré avec succès : {os.path.abspath(pdf_filename)}")
