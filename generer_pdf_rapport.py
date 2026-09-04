# -*- coding: utf-8 -*-
"""
generer_pdf_rapport.py
Génère le PDF exact du premier rapport avec ReportLab
"""
import sys, os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

pdf_filename = "Rapport_de_Stage_Premier.pdf"
doc = SimpleDocTemplate(
    pdf_filename,
    pagesize=letter,
    rightMargin=40,
    leftMargin=40,
    topMargin=40,
    bottomMargin=40
)

styles = getSampleStyleSheet()

# Styles personnalisés
title_style = ParagraphStyle(
    'DocTitle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=20,
    leading=24,
    textColor=colors.HexColor('#003366'),
    alignment=1,
    spaceAfter=10
)

subtitle_style = ParagraphStyle(
    'DocSubtitle',
    parent=styles['Normal'],
    fontName='Helvetica-Oblique',
    fontSize=11,
    leading=14,
    textColor=colors.HexColor('#0066CC'),
    alignment=1,
    spaceAfter=20
)

h1_style = ParagraphStyle(
    'H1',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=14,
    leading=18,
    textColor=colors.HexColor('#003366'),
    spaceBefore=15,
    spaceAfter=8
)

h2_style = ParagraphStyle(
    'H2',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=12,
    leading=15,
    textColor=colors.HexColor('#0066CC'),
    spaceBefore=10,
    spaceAfter=6
)

body_style = ParagraphStyle(
    'Body',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=9.5,
    leading=13,
    textColor=colors.HexColor('#333333'),
    spaceAfter=6
)

bullet_style = ParagraphStyle(
    'Bullet',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=9.5,
    leading=13,
    textColor=colors.HexColor('#333333'),
    leftIndent=15,
    spaceAfter=4
)

code_style = ParagraphStyle(
    'Code',
    parent=styles['Normal'],
    fontName='Courier',
    fontSize=8,
    leading=10,
    textColor=colors.HexColor('#222222'),
    backColor=colors.HexColor('#F4F4F4'),
    borderColor=colors.HexColor('#DDDDDD'),
    borderWidth=0.5,
    borderPadding=6,
    spaceBefore=6,
    spaceAfter=6
)

story = []

# Title
story.append(Paragraph("RAPPORT DE STAGE ET DE RÉALISATION TECHNIQUE", title_style))
story.append(Paragraph("<b>Sujet :</b> Développement du Module d'Ingestion Intelligente de CV (PDF / DOCX / OCR)<br/><b>Projet :</b> Agent IA RH — RecrutIA | <b>Entreprise :</b> ArtiWeb (Fès)", subtitle_style))
story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#003366'), spaceAfter=15))

# Section I
story.append(Paragraph("I. PRÉSENTATION DE L'ENTREPRISE D'ACCUEIL : ARTIWEB", h1_style))
story.append(Paragraph("1.1 Présentation Générale", h2_style))
story.append(Paragraph("• <b>Nom de l'entreprise :</b> ARTIWEB (ARTI web)", bullet_style))
story.append(Paragraph("• <b>Site Web Officiel :</b> https://artiweb.ma/", bullet_style))
story.append(Paragraph("• <b>Siège Social :</b> Fès, Maroc", bullet_style))
story.append(Paragraph("• <b>Partenariats Clés :</b> Partenaire Google (Google Partner)", bullet_style))
story.append(Paragraph("• <b>Horaires d'ouverture :</b> Lundi – Vendredi (9:00 – 21:00)", bullet_style))
story.append(Paragraph("• <b>Contact :</b> (+212) 664-017447 | contact@artiweb.ma", bullet_style))

story.append(Paragraph("1.2 Secteurs d'Activité et Expertises", h2_style))
story.append(Paragraph("ArtiWeb est une agence de communication et de marketing digital basée à Fès. Ses domaines d'expertise couvrent :", body_style))
story.append(Paragraph("1. <b>Stratégie Digitale & Marketing Numérique :</b> Accompagnement dans le développement de l'image de marque.", bullet_style))
story.append(Paragraph("2. <b>Développement Web & Applications :</b> Sites sur-mesure, e-commerce et applications métiers.", bullet_style))
story.append(Paragraph("3. <b>Référencement (SEO / SEM / Social Ads) :</b> Google Ads et visibilité sur moteurs de recherche.", bullet_style))
story.append(Paragraph("4. <b>Marketplace & Studio Marketing :</b> Solutions e-commerce et contenu multimédia.", bullet_style))

# Section II
story.append(Paragraph("II. FICHE PROJET : AGENT IA RH (RECRUTIA)", h1_style))
story.append(Paragraph("2.1 Nom du projet", h2_style))
story.append(Paragraph("Agent IA RH — Système intelligent d'automatisation du processus de recrutement (RecrutIA).", body_style))

story.append(Paragraph("2.2 Problématique", h2_style))
story.append(Paragraph("Le tri manuel des candidatures est chronophage, sujet aux erreurs et biais, et manque de traçabilité lors des gros volumes. <i>Question centrale : Comment automatiser le tri tout en gardant une décision fiable et sous contrôle humain ?</i>", body_style))

story.append(Paragraph("2.3 Architecture Globale en 3 Couches", h2_style))
story.append(Paragraph("1. <b>Couche d'Ingestion (Tâche réalisée) :</b> Extraction et structuration des CV bruts sans LLM.", bullet_style))
story.append(Paragraph("2. <b>Couche IA Agentique :</b> Comparaison sémantique, score de correspondance et justification.", bullet_style))
story.append(Paragraph("3. <b>Couche de Supervision Humaine :</b> Le RH garde la décision finale sur chaque proposition.", bullet_style))

# Section III
story.append(Paragraph("III. DESCRIPTION DÉTAILLÉE DE LA TÂCHE : COUCHE D'INGESTION", h1_style))
story.append(Paragraph("3.1 Objectif et Enjeux", h2_style))
story.append(Paragraph("Développer un module Python autonome pour transformer un CV brut (PDF/DOCX/Scan) en dictionnaire structuré JSON sans dépendre d'un LLM.", body_style))

story.append(Paragraph("3.2 Technologies Utilisées", h2_style))

table_data = [
    [Paragraph("<b>Bibliothèque / Outil</b>", body_style), Paragraph("<b>Rôle Technique dans le Projet</b>", body_style)],
    [Paragraph("Python 3.12", body_style), Paragraph("Langage principal de développement backend.", body_style)],
    [Paragraph("pdfplumber", body_style), Paragraph("Extraction haute précision du texte natif et de la mise en page PDF.", body_style)],
    [Paragraph("PyMuPDF (fitz)", body_style), Paragraph("Extraction rapide et conversion des pages en images HD pour l'OCR.", body_style)],
    [Paragraph("python-docx", body_style), Paragraph("Parsing des paragraphes et des tableaux dans les fichiers Word (.docx).", body_style)],
    [Paragraph("pytesseract (OCR)", body_style), Paragraph("Moteur OCR de Google pour traiter les CV scannés/images.", body_style)],
    [Paragraph("unicodedata & re", body_style), Paragraph("Normalisation Unicode NFC, suppression du bruit et Regex.", body_style)],
    [Paragraph("pytest & unittest", body_style), Paragraph("Suite de 21 tests automatisés pour valider le code.", body_style)]
]

t = Table(table_data, colWidths=[150, 370])
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
story.append(t)
story.append(Spacer(1, 10))

story.append(Paragraph("3.3 Le Pipeline en 4 Étapes", h2_style))
story.append(Paragraph("1. <b>Extraction en Cascade :</b> pdfplumber / python-docx -> PyMuPDF -> Fallback OCR Tesseract si &lt; 80 chars.", bullet_style))
story.append(Paragraph("2. <b>Nettoyage & Normalisation :</b> Unicode NFC, fusion des mots coupés, correction ligatures (ﬁ -&gt; fi), suppression puces.", bullet_style))
story.append(Paragraph("3. <b>Parsing NLP & Motif Matching :</b> Compétences via competences_ref.json, expérience par dates, diplômes hiérarchisés.", bullet_style))
story.append(Paragraph("4. <b>Assemblage JSON :</b> Dictionnaire structuré propre prêt pour la couche IA.", bullet_style))

# Section IV
story.append(Paragraph("IV. RÉSULTATS DES TESTS ET VALIDATION EXPÉRIMENTALE", h1_style))
story.append(Paragraph("4.1 Validation sur 21 Tests Automatisés", h2_style))
story.append(Paragraph("• <b>TestCleaner (5 tests) :</b> Valide la suppression du bruit, espaces et ligatures.", bullet_style))
story.append(Paragraph("• <b>TestParser (9 tests) :</b> Valide le calcul des compétences, durées d'expérience et diplômes.", bullet_style))
story.append(Paragraph("• <b>TestIntegration (7 tests) :</b> Valide tout le pipeline sur de vrais PDF/DOCX virtuels.", bullet_style))
story.append(Paragraph("<b>Résultat : 21/21 tests validés avec succès (100% en 0.91 seconde).</b>", body_style))

story.append(Paragraph("4.2 Validation sur le CV Réel (MEKKI_FATIMA-EZAHRAE_AI_Backend.pdf)", h2_style))
story.append(Paragraph("• <b>Statut :</b> SUCCÈS | <b>Durée :</b> 0.782s", bullet_style))
story.append(Paragraph("• <b>Formation :</b> Master / Ingénieur (Détecté 'Ingénieure en Génie Informatique')", bullet_style))
story.append(Paragraph("• <b>Expérience :</b> 2 an(s) (Calculé automatiquement)", bullet_style))
story.append(Paragraph("• <b>Compétences (33 détectées) :</b> Python, Django, Flask, TensorFlow, React, Azure, Java, MySQL, Node.js, Scikit-learn, etc.", bullet_style))

code_json = """{
    "fichier": "MEKKI_FATIMA-EZAHRAE_AI_Backend.pdf",
    "statut": "succès",
    "formation": "Master / Ingénieur",
    "experience_annees": 2,
    "nb_competences": 33,
    "competences": ["Azure", "Bootstrap", "CSS", "Cloud", "Computer Vision", "Django", "Flask", "Python", "React", ...],
    "duree_traitement": "0.782 s"
}"""
story.append(Paragraph(code_json.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))

# Section V
story.append(Paragraph("V. CONCLUSION ET PERSPECTIVES", h1_style))
story.append(Paragraph("Le module d'ingestion développé pour <b>ArtiWeb</b> est complet, autonome, ultra-rapide (&lt; 1s) et validé. Il fournit le contrat de données JSON prêt pour la couche d'IA Agentique (Couche 2).", body_style))

doc.build(story)
print(f"PDF généré avec succès : {os.path.abspath(pdf_filename)}")
