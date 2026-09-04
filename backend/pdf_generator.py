"""
Module : pdf_generator.py
Rôle   : Génère une fiche de synthèse PDF professionnelle pour une candidature RH.
"""

import os
import tempfile
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

NAVY    = colors.HexColor('#0F172A')
PRIMARY = colors.HexColor('#059669')
GRAY    = colors.HexColor('#475569')
LGRAY   = colors.HexColor('#F4F7F6')
BORDER  = colors.HexColor('#E2E8F0')
WHITE   = colors.white

st_title = ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=NAVY, spaceAfter=4)
st_sub   = ParagraphStyle('sub', fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=PRIMARY, spaceAfter=10)
st_h2    = ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=NAVY, spaceBefore=10, spaceAfter=4)
st_body  = ParagraphStyle('body', fontName='Helvetica', fontSize=9.5, leading=13.5, textColor=GRAY, spaceAfter=4)
st_cell  = ParagraphStyle('cell', fontName='Helvetica', fontSize=9, leading=12, textColor=GRAY, alignment=1)
st_cellb = ParagraphStyle('cellb', fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=NAVY, alignment=1)


def generer_pdf_candidature(candidature_data: dict, candidat_nom: str, offre_titre: str) -> str:
    """Génère un rapport PDF d'évaluation RH et retourne le chemin du fichier temporaire."""
    fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    story = []

    story.append(Paragraph("RECRUTIA RH — RAPPORT SYNTHÉTIQUE D'ÉVALUATION IA", st_sub))
    story.append(Paragraph(f"Candidat : {candidat_nom}", st_title))
    story.append(Paragraph(f"Poste visé : <b>{offre_titre}</b>", st_body))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=12, spaceBefore=6))

    raw = candidature_data.get("raw_ingestion_json") or {}
    score = candidature_data.get("score", 0.0)
    decision = candidature_data.get("decision_rh", "EN_ATTENTE")

    kpis = [
        [Paragraph("Score IA", st_cellb), Paragraph("Expérience", st_cellb), Paragraph("Formation", st_cellb), Paragraph("Décision RH", st_cellb)],
        [Paragraph(f"<b>{score}/100</b>", st_cell), Paragraph(f"{raw.get('experience_annees', 0)} an(s)", st_cell), Paragraph(f"{raw.get('formation', 'N/A')}", st_cell), Paragraph(f"<b>{decision}</b>", st_cell)]
    ]
    t_kpi = Table(kpis, colWidths=[4*cm, 4*cm, 5*cm, 4.5*cm])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), LGRAY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 10))

    # Compétences
    story.append(Paragraph("COMPÉTENCES DÉTECTÉES SUR LE CV", st_h2))
    comps = ", ".join(raw.get("competences", [])) or "Aucune compétence majeure détectée."
    story.append(Paragraph(comps, st_body))
    story.append(Spacer(1, 8))

    # Justification IA
    story.append(Paragraph("JUSTIFICATION RH & EXPLICABILITÉ IA", st_h2))
    justif = candidature_data.get("justification_ia") or "Aucune justification disponible."
    story.append(Paragraph(justif.replace("\n", "<br/>"), st_body))
    story.append(Spacer(1, 8))

    # Note RH
    if candidature_data.get("note_rh"):
        story.append(Paragraph("NOTE ET REMARQUES DU RECRUTEUR RH", st_h2))
        story.append(Paragraph(candidature_data.get("note_rh"), st_body))
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=6, spaceBefore=12))
    story.append(Paragraph("Document confidentiel généré par RecrutIA RH — ArtiWeb Fès (Google Partner)", ParagraphStyle('foot', fontName='Helvetica-Oblique', fontSize=8, textColor=GRAY, alignment=1)))

    doc.build(story)
    return pdf_path
