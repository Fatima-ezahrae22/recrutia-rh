# -*- coding: utf-8 -*-
"""
generer_rapport_final_detaille.py
Génère le rapport PDF complet du projet Agent IA RH
Tâches 1 (Ingestion), 2 (IA Agentique) & 3 (Backend FastAPI & DB)
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)

# ── Couleurs ────────────────────────────────────────────────
NAVY  = colors.HexColor('#003366')
BLUE  = colors.HexColor('#0055A4')
GREEN = colors.HexColor('#006633')
RED   = colors.HexColor('#CC0000')
AMBER = colors.HexColor('#CC6600')
GRAY  = colors.HexColor('#333333')
LGRAY = colors.HexColor('#F2F4F7')
BGCOD = colors.HexColor('#F0F4F8')
WHITE = colors.white

# ── Styles ──────────────────────────────────────────────────
st_cover   = ParagraphStyle('cover',   fontName='Helvetica-Bold',    fontSize=20, leading=24, textColor=NAVY,  alignment=1, spaceAfter=8)
st_sub     = ParagraphStyle('sub',     fontName='Helvetica-Oblique', fontSize=11, leading=14, textColor=BLUE,  alignment=1, spaceAfter=16)
st_h1      = ParagraphStyle('h1',      fontName='Helvetica-Bold',    fontSize=14, leading=17, textColor=NAVY,  spaceBefore=16, spaceAfter=6)
st_h2      = ParagraphStyle('h2',      fontName='Helvetica-Bold',    fontSize=11, leading=14, textColor=BLUE,  spaceBefore=10, spaceAfter=4)
st_h3      = ParagraphStyle('h3',      fontName='Helvetica-Bold',    fontSize=10, leading=13, textColor=GREEN, spaceBefore=7,  spaceAfter=3)
st_body    = ParagraphStyle('body',    fontName='Helvetica',         fontSize=9.5, leading=13.5, textColor=GRAY, spaceAfter=5)
st_bullet  = ParagraphStyle('bullet',  fontName='Helvetica',         fontSize=9.5, leading=13,   textColor=GRAY, leftIndent=14, spaceAfter=3)
st_code    = ParagraphStyle('code',    fontName='Courier',           fontSize=8,   leading=10,   textColor=colors.HexColor('#111111'),
                             backColor=BGCOD, borderColor=colors.HexColor('#BBBBBB'), borderWidth=0.5,
                             borderPadding=6, spaceBefore=5, spaceAfter=7)
st_note    = ParagraphStyle('note',    fontName='Helvetica-Oblique', fontSize=8.5, leading=12, textColor=colors.HexColor('#555555'),
                             backColor=colors.HexColor('#FFF8E1'), borderColor=colors.HexColor('#DDAA00'),
                             borderWidth=0.5, borderPadding=5, leftIndent=8, spaceAfter=7)
st_ok      = ParagraphStyle('ok',      fontName='Helvetica-Bold',    fontSize=9.5, textColor=GREEN)
st_err     = ParagraphStyle('err',     fontName='Helvetica-Bold',    fontSize=9.5, textColor=RED)
st_cell    = ParagraphStyle('cell',    fontName='Helvetica',         fontSize=9,   leading=12, textColor=GRAY)
st_cellh   = ParagraphStyle('cellh',   fontName='Helvetica-Bold',    fontSize=9,   leading=12, textColor=WHITE)
st_thdr    = ParagraphStyle('thdr',    fontName='Helvetica-Bold',    fontSize=9.5, leading=12, textColor=WHITE)

# ── Helpers simples ──────────────────────────────────────────
def p(t, st=None):  return Paragraph(t, st or st_body)
def b(t):           return Paragraph(f"• {t}", st_bullet)
def bb(pre, t):     return Paragraph(f"<b>{pre}</b> {t}", st_bullet)
def h1(t):          return Paragraph(t, st_h1)
def h2(t):          return Paragraph(t, st_h2)
def h3(t):          return Paragraph(t, st_h3)
def hr():           return HRFlowable(width="100%", thickness=1.2, color=NAVY, spaceAfter=8, spaceBefore=2)
def hr2():          return HRFlowable(width="100%", thickness=0.4, color=colors.HexColor('#CCCCCC'), spaceAfter=5)
def sp(n=8):        return Spacer(1, n)
def code(t):        return Paragraph(t.replace(' ','&nbsp;').replace('\n','<br/>'), st_code)
def note(t):        return Paragraph(f"<i>Info : {t}</i>", st_note)

W = 15.5*cm

def ttable(rows, widths):
    t = Table(rows, colWidths=widths)
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(-1,0),  NAVY),
        ('TEXTCOLOR',    (0,0),(-1,0),  WHITE),
        ('FONTNAME',     (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0,0),(-1,-1), 9),
        ('ALIGN',        (0,0),(-1,-1), 'LEFT'),
        ('VALIGN',       (0,0),(-1,-1), 'TOP'),
        ('GRID',         (0,0),(-1,-1), 0.4, colors.HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE, LGRAY]),
        ('TOPPADDING',   (0,0),(-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
        ('LEFTPADDING',  (0,0),(-1,-1), 6),
    ]))
    return t

def rbox(titre, lignes, c=GREEN):
    rows = [[p(f"<b>{titre}</b>", st_thdr)]]
    for l in lignes:
        rows.append([p(l, st_cell)])
    t = Table(rows, colWidths=[W])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), c),
        ('BACKGROUND',(0,1),(-1,-1), LGRAY),
        ('BOX',       (0,0),(-1,-1), 0.8, c),
        ('TOPPADDING',   (0,0),(-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
        ('LEFTPADDING',  (0,0),(-1,-1), 8),
    ]))
    return t

# ════════════════════════════════════════════════════════════
# CONTENU DU RAPPORT
# ════════════════════════════════════════════════════════════
story = []

# ── PAGE DE GARDE ────────────────────────────────────────────
story += [
    sp(30),
    p("RAPPORT DE STAGE ET DOCUMENTATION TECHNIQUE", st_cover),
    p("Projet Agent IA RH (RecrutIA)", st_sub),
    hr(),
    sp(6),
    p("Tâche 1 — Module d'Ingestion Intelligente de CV (PDF / DOCX / OCR)<br/>Tâche 2 — Module d'Évaluation IA Agentique &amp; Scoring Sémantique<br/>Tâche 3 — Backend API REST FastAPI, Base de Données &amp; Traçabilité", st_sub),
    sp(20),
]
info = [
    [p("<b>Entreprise</b>", st_cell), p("ARTIWEB — Agence Communication &amp; Marketing Digital, Fès, Maroc", st_cell)],
    [p("<b>Site web</b>",   st_cell), p("https://artiweb.ma", st_cell)],
    [p("<b>Contact</b>",    st_cell), p("contact@artiweb.ma | (+212) 664-017447", st_cell)],
    [p("<b>Partenariat</b>",st_cell), p("Google Partner certifié", st_cell)],
    [p("<b>Projet</b>",     st_cell), p("Agent IA RH / RecrutIA — Automatisation intelligente du recrutement", st_cell)],
    [p("<b>Technologies</b>",st_cell),p("Python 3.12 | FastAPI | SQLAlchemy | PostgreSQL / SQLite | Pydantic V2 | pdfplumber | PyMuPDF | sentence-transformers", st_cell)],
]
tg = Table(info, colWidths=[3.5*cm, 12*cm])
tg.setStyle(TableStyle([
    ('BOX',       (0,0),(-1,-1),1,NAVY),
    ('INNERGRID', (0,0),(-1,-1),0.3,colors.HexColor('#AAAAAA')),
    ('BACKGROUND',(0,0),(0,-1), LGRAY),
    ('TOPPADDING',(0,0),(-1,-1),6),
    ('BOTTOMPADDING',(0,0),(-1,-1),6),
    ('LEFTPADDING',(0,0),(-1,-1),8),
    ('FONTSIZE',  (0,0),(-1,-1),9),
]))
story += [tg, sp(20), PageBreak()]

# ── I. ARTIWEB & PROJET ──────────────────────────────────────
story += [h1("I. PRÉSENTATION ARTIWEB ET ARCHITECTURE 3 COUCHES"), hr(),
    p("ARTIWEB est une agence de communication et marketing digital basée à Fès (Google Partner). Le projet <b>RecrutIA</b> a été conçu avec une architecture modulaire à 3 couches :"),
    sp(6),
]
arch = [
    [p("<b>Couche</b>",st_cellh), p("<b>Rôle</b>",st_cellh), p("<b>Statut</b>",st_cellh)],
    [p("<b>1 — Ingestion</b>",st_cell), p("Transformer un CV brut (PDF/DOCX/Scan) en dictionnaire JSON structuré sans LLM.",st_cell), p("<b>RÉALISÉE</b>", st_ok)],
    [p("<b>2 — IA Agentique</b>",st_cell), p("Évaluer correspondance candidat/offre : score 0–100 + justification argumentée.",st_cell), p("<b>RÉALISÉE</b>", st_ok)],
    [p("<b>3 — Backend API REST</b>",st_cell), p("Connecter Tâches 1 &amp; 2 avec base de données (PostgreSQL/SQLite), Swagger &amp; Audit.",st_cell), p("<b>RÉALISÉE</b>", st_ok)],
]
story += [ttable(arch,[3.5*cm,9*cm,3*cm]), sp(10)]

# ── II. TÂCHE 1 ──────────────────────────────────────────────
story += [h1("II. TÂCHE 1 — COUCHE D'INGESTION INTELLIGENTE DE CV"), hr(),
    p("Module Python autonome (ingestion/) :"),
    bb("Cascade 3 niveaux :", "pdfplumber (texte natif) ➔ PyMuPDF (secours) ➔ OCR Tesseract 300 DPI (scans). Fichiers Word via python-docx."),
    bb("Nettoyage Unicode NFC :", "Suppression des ligatures PDF (fi, fl), icônes (•, ★) et fusion des mots coupés en fin de ligne."),
    bb("Parsing NLP :", "Matching competences_ref.json, fusion des dates d'expérience et hiérarchie diplômes (PhD > Master > Licence > BTS)."),
    bb("Validation :", "21/21 tests automatisés PASSED en 0.91s."),
    sp(8),
]

# ── III. TÂCHE 2 ─────────────────────────────────────────────
story += [h1("III. TÂCHE 2 — COUCHE IA AGENTIQUE &amp; SCORING SÉMANTIQUE"), hr(),
    p("Module Python autonome (ia_agentic/) :"),
    bb("Filtre Critères Durs :", "Élimination immédiate (Score 0.0, statut rejete_auto_filtre) si expérience < minimum ou compétences obligatoires manquantes."),
    bb("Embeddings &amp; Cosine Similarity :", "Vectorisation all-MiniLM-L6-v2 + score combiné (40% vectoriel + 40% compétences + 20% expérience)."),
    bb("Justification LLM anti-hallucination :", "Groq API / Ollama / Fallback déterministe basé strictement sur les faits du CV."),
    bb("Validation :", "7/7 tests automatisés PASSED sur 3 scénarios (bon match, rejet dur, match modéré)."),
    sp(10), PageBreak(),
]

# ── IV. TÂCHE 3 ──────────────────────────────────────────────
story += [h1("IV. TÂCHE 3 — BACKEND FASTAPI, BASE DE DONNÉES &amp; TRAÇABILITÉ"), hr(),
    h2("4.1 Objectif de la Tâche 3"),
    p("Développer l'API REST backend (backend/) qui orchestre les Couches 1 et 2 au sein d'un système fluide, persistant et auditable en base de données."),
    sp(4),
    h2("4.2 Comment Exécuter et Tester la Tâche 3"),
    h3("Commande A — Démarrer le serveur API Backend (FastAPI + Swagger UI) :"),
    code("cd C:\\Users\\oo\\OneDrive\\Bureau\\agent_ai\npython run_backend.py"),
    p("Accès Swagger UI Documentation : <b>http://127.0.0.1:8000/docs</b>"),
    h3("Commande B — Lancer la suite de 35 tests automatisés (Tâches 1, 2 &amp; 3) :"),
    code("python -m pytest tests/ -v"),
    sp(6),
    h2("4.3 Architecture des Fichiers Backend (backend/)"),
    code("agent_ai/\n├── backend/\n│   ├── __init__.py           # Export principal\n│   ├── database.py         # SQLAlchemy DB Config (PostgreSQL / SQLite fallback)\n│   ├── models.py           # ORM Tables: Offre, Candidat, Candidature, AuditLog\n│   ├── schemas.py          # Pydantic V2 Schemas pour requêtes/réponses API\n│   ├── pipeline.py         # Connecteur end-to-end (Tâche 1 ➔ Tâche 2 ➔ DB)\n│   └── main.py             # Application FastAPI + endpoints REST\n├── tests/\n│   ├── test_ingestion.py   # 21 tests Couche 1\n│   ├── test_ia_agentic.py  # 7 tests Couche 2\n│   └── test_backend.py     # 7 tests d'intégration API REST FastAPI (TestClient)\n└── run_backend.py          # Script d'exécution Uvicorn"),
    h2("4.4 Endpoints API REST Exposés"),
    sp(4),
]

endpoints = [
    [p("<b>Méthode &amp; Route</b>",st_cellh), p("<b>Description</b>",st_cellh), p("<b>Traçabilité Audit</b>",st_cellh)],
    [p("<code>POST /api/offres</code>",st_cell), p("Création d'une offre d'emploi RH avec ses critères (exp min, compétences).",st_cell), p("OFFRE_CREEE",st_cell)],
    [p("<code>GET /api/offres</code>",st_cell), p("Lister toutes les offres d'emploi enregistrées.",st_cell), p("Lecture",st_cell)],
    [p("<code>POST /api/candidatures</code>",st_cell), p("Upload du CV (.pdf/.docx) + offre_id. Déclenche le pipeline automatique Tâche 1 ➔ Tâche 2 ➔ DB.",st_cell), p("CANDIDATURE_SOUMISE",st_cell)],
    [p("<code>GET /api/offres/{id}/candidatures</code>",st_cell), p("Lister les candidatures d'une offre, TRIÉES PAR SCORE DÉCROISSANT.",st_cell), p("Consultation RH",st_cell)],
    [p("<code>GET /api/candidatures/{id}</code>",st_cell), p("Consulter la fiche détaillée d'une candidature (score, justification, JSON brut).",st_cell), p("Consultation RH",st_cell)],
    [p("<code>PATCH /api/candidatures/{id}/decision</code>",st_cell), p("Enregistrer la décision RH (VALIDE, CORRIGE, REJETE) avec note et utilisateur.",st_cell), p("DECISION_RH_...",st_cell)],
    [p("<code>GET /api/audit</code>",st_cell), p("Consulter l'historique complet d'audit de toutes les actions système et RH.",st_cell), p("Audit &amp; Compliance",st_cell)],
]
story += [ttable(endpoints,[4.5*cm,8*cm,3*cm]), sp(8)]

story += [h2("4.5 Résultats des Tests Backend &amp; Validation Globale"),
    sp(4),
]

story += [
    rbox("✅ RESULTAT TÂCHE 3 — 7 TESTS FASTAPI PASSED (tests/test_backend.py)", [
        "test_01_health_check             : GET / (Statut API 200 OK)",
        "test_02_creer_offre              : POST /api/offres (Offre créée et ID retourné)",
        "test_03_lister_offres             : GET /api/offres (Listing d'offres)",
        "test_04_soumettre_candidature     : POST /api/candidatures (Upload PDF + Ingestion ➔ Scoring ➔ DB)",
        "test_05_lister_candidatures_triees: GET /api/offres/{id}/candidatures (Tri par score décroissant)",
        "test_06_enregistrer_decision_rh   : PATCH /api/candidatures/{id}/decision (Décision VALIDE + Note)",
        "test_07_consulter_audit_log       : GET /api/audit (Logs d'actions d'audit)",
        "RÉSULTAT BACKEND                  : 7/7 PASSED — 100% de réussite",
    ], GREEN),
    sp(6),
    rbox("🏆 RÉSULTAT GLOBAL DU PROJET — 35 TESTS AUTOMATISÉS PASSED", [
        "tests/test_ingestion.py  (Tâche 1) : 21 / 21 tests PASSED",
        "tests/test_ia_agentic.py (Tâche 2) :  7 /  7 tests PASSED",
        "tests/test_backend.py   (Tâche 3) :  7 /  7 tests PASSED",
        "TOTAL DU SUITE PROJET            : 35 / 35 TESTS PASSED — 100% — Exec: 3.69 secondes",
    ], GREEN),
    sp(10),
    h1("V. CONCLUSION"), hr(),
    p("Les **Tâches 1, 2 et 3 sont 100% finalisées, intégrées et validées par 35 tests automatisés**. Le serveur API REST FastAPI fonctionne de bout en bout et offre les interfaces documentées Swagger UI pour le futur Dashboard (Tâche 4)."),
]

# ── Build ────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    "Rapport_Final_Agent_IA_RH.pdf",
    pagesize=A4,
    rightMargin=2*cm, leftMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm
)
doc.build(story)
print("PDF final genere avec succes : Rapport_Final_Agent_IA_RH.pdf")
