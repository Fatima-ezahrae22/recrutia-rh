"""
Module : email_service.py
Rôle   : Service d'envoi et de génération des emails professionnels de convocation d'entretien.
         Supporte l'envoi SMTP réel si configuré dans .env, avec un fallback de journalisation sécurisé pour la démonstration.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Charger automatiquement le fichier .env
load_dotenv()

logger = logging.getLogger("RecrutIA.Email")

def get_smtp_config():
    return {
        "host": os.environ.get("SMTP_HOST", ""),
        "port": int(os.environ.get("SMTP_PORT", 587)),
        "user": os.environ.get("SMTP_USER", ""),
        "pass": os.environ.get("SMTP_PASS", ""),
        "sender": os.environ.get("SENDER_EMAIL", "recrutement@artiweb.ma")
    }


def generer_html_convocation(
    nom_candidat: str,
    titre_offre: str,
    date_heure: str,
    format_entretien: str,
    lieu_ou_lien: str,
    message_personnalise: str = None
) -> str:
    """Génère le modèle d'email HTML professionnel de convocation."""
    type_format = "en nos locaux à Fès" if format_entretien.upper() == "PRESENTIEL" else "en visioconférence (Google Meet)"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #0F172A; background-color: #F8FAFC; padding: 20px; }}
        .card {{ background-color: #ffffff; border: 1px solid #E2E8F0; border-radius: 12px; max-width: 600px; margin: 0 auto; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        .header {{ border-bottom: 2px solid #059669; padding-bottom: 16px; margin-bottom: 24px; }}
        .brand {{ font-size: 20px; font-weight: 800; color: #059669; }}
        .title {{ font-size: 18px; font-weight: 700; color: #0F172A; margin-top: 8px; }}
        .content {{ line-height: 1.6; font-size: 14px; color: #334155; }}
        .details-box {{ background-color: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; padding: 16px; margin: 20px 0; }}
        .detail-item {{ font-size: 14px; margin-bottom: 8px; }}
        .detail-item strong {{ color: #047857; }}
        .footer {{ border-top: 1px solid #E2E8F0; margin-top: 24px; padding-top: 16px; font-size: 12px; color: #94A3B8; text-align: center; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <div class="brand">RecrutIA RH</div>
          <div class="title">Convocation à un entretien de recrutement</div>
        </div>
        <div class="content">
          <p>Bonjour <strong>{nom_candidat}</strong>,</p>
          <p>Suite à l'analyse de votre candidature pour le poste de <strong>{titre_offre}</strong>, nous avons le plaisir de vous informer que votre profil a été retenu pour l'étape suivante.</p>
          
          <div class="details-box">
            <div class="detail-item">📅 <strong>Date et Heure :</strong> {date_heure}</div>
            <div class="detail-item">📍 <strong>Format :</strong> Entretien {type_format}</div>
            <div class="detail-item">🗺️ <strong>Lieu / Lien :</strong> {lieu_ou_lien}</div>
          </div>
          
          {f"<p><em>Message de l'équipe RH :</em> {message_personnalise}</p>" if message_personnalise else ""}
          
          <p>Merci de bien vouloir nous confirmer votre présence en répondant à cet e-mail.</p>
          <p>Cordialement,<br><strong>L'Équipe RecrutIA RH</strong></p>
        </div>
        <div class="footer">
          RecrutIA — Système Intelligent d'Automatisation & Scoring du Recrutement
        </div>
      </div>
    </body>
    </html>
    """
    return html


def envoyer_email_convocation(
    destinataire_email: str,
    nom_candidat: str,
    titre_offre: str,
    date_heure: str,
    format_entretien: str,
    lieu_ou_lien: str,
    message_personnalise: str = None
) -> dict:
    """
    Tente d'envoyer l'email via SMTP réel si configuré dans .env,
    ou simule et enregistre l'envoi avec succès pour la démo.
    """
    cfg = get_smtp_config()
    html_content = generer_html_convocation(
        nom_candidat=nom_candidat,
        titre_offre=titre_offre,
        date_heure=date_heure,
        format_entretien=format_entretien,
        lieu_ou_lien=lieu_ou_lien,
        message_personnalise=message_personnalise
    )

    candidat_email = destinataire_email or "candidat@email.com"

    # Tentative d'envoi SMTP réel si serveur configuré dans .env
    if cfg["host"] and cfg["user"] and cfg["pass"]:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Convocation Entretien — {titre_offre} (ArtiWeb)"
            msg["From"] = cfg["sender"] or cfg["user"]
            msg["To"] = candidat_email
            msg.attach(MIMEText(html_content, "html"))

            if cfg["port"] == 465:
                with smtplib.SMTP_SSL(cfg["host"], cfg["port"]) as server:
                    server.login(cfg["user"], cfg["pass"])
                    server.sendmail(cfg["sender"], [candidat_email], msg.as_string())
            else:
                with smtplib.SMTP(cfg["host"], cfg["port"]) as server:
                    server.starttls()
                    server.login(cfg["user"], cfg["pass"])
                    server.sendmail(cfg["sender"], [candidat_email], msg.as_string())

            logger.info(f"[Email] ✅ Email RÉEL envoyé à {candidat_email} via SMTP ({cfg['host']}).")
            return {"statut": "envoye_smtp", "destinataire": candidat_email, "mode": f"SMTP Réel ({cfg['host']})"}
        except Exception as e:
            logger.error(f"[Email] Échec SMTP ({e}). Basculement sur le mode Démo sécurisé.")

    # Mode Démo / Fallback
    logger.info(f"[Email Simulé] 📧 Convocation générée pour {candidat_email} (Offre: '{titre_offre}', Date: {date_heure})")
    return {
        "statut": "envoye_demo",
        "destinataire": candidat_email,
        "mode": "Simulation Démo Réussie",
        "html_preview": html_content
    }


# ─────────────────────────────────────────────────────────────────────────────
# EMAIL EMBAUCHE — Confirmation officielle de recrutement
# ─────────────────────────────────────────────────────────────────────────────

def generer_html_embauche(
    nom_candidat: str,
    titre_offre: str,
    agence: str = "ArtiWeb Fès",
    note_rh: str = None,
    score_ia: float = None
) -> str:
    """Génère un email HTML professionnel de confirmation d'embauche."""
    score_section = ""
    if score_ia is not None:
        score_section = f"""
        <div style="text-align:center; margin: 20px 0;">
          <div style="display:inline-block; background:linear-gradient(135deg,#10B981,#059669);
               color:#fff; border-radius:50%; width:80px; height:80px;
               line-height:80px; font-size:24px; font-weight:900; font-family:sans-serif;">
            {round(score_ia)}%
          </div>
          <div style="font-size:11px; color:#6B7280; margin-top:6px; text-transform:uppercase; letter-spacing:1px;">
            Score d'Adéquation IA
          </div>
        </div>"""

    note_section = ""
    if note_rh:
        note_section = f"""
        <div style="background:#F0FDF4; border-left:4px solid #10B981; border-radius:0 8px 8px 0;
             padding:14px 16px; margin:16px 0; font-size:13px; color:#065F46; font-style:italic;">
          <strong>Message de l'équipe RH :</strong><br>{note_rh}
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif; color:#0F172A; background:#F0FDF4; padding:24px; }}
    .card {{ background:#ffffff; border:1px solid #A7F3D0; border-radius:16px; max-width:620px;
             margin:0 auto; overflow:hidden; box-shadow:0 20px 40px rgba(16,185,129,0.12); }}
    .hero {{ background:linear-gradient(135deg,#10B981 0%,#059669 100%); padding:40px 32px; text-align:center; }}
    .hero-icon {{ font-size:48px; margin-bottom:12px; }}
    .hero-title {{ color:#fff; font-size:26px; font-weight:900; font-family:'Segoe UI',sans-serif; margin:0; }}
    .hero-sub {{ color:rgba(255,255,255,0.85); font-size:14px; margin-top:6px; }}
    .body {{ padding:32px; }}
    .greeting {{ font-size:16px; line-height:1.6; color:#1E293B; margin-bottom:20px; }}
    .details-box {{ background:#ECFDF5; border:1px solid #6EE7B7; border-radius:10px; padding:20px; margin:20px 0; }}
    .detail-row {{ display:flex; align-items:flex-start; gap:10px; font-size:14px; margin-bottom:10px; color:#065F46; }}
    .detail-row:last-child {{ margin-bottom:0; }}
    .detail-label {{ font-weight:700; min-width:100px; }}
    .steps {{ margin:24px 0; }}
    .step {{ display:flex; gap:14px; margin-bottom:16px; align-items:flex-start; }}
    .step-num {{ background:linear-gradient(135deg,#10B981,#059669); color:#fff; border-radius:50%;
                 width:28px; height:28px; min-width:28px; display:flex; align-items:center;
                 justify-content:center; font-size:12px; font-weight:800; }}
    .step-text {{ font-size:13.5px; line-height:1.55; color:#334155; padding-top:4px; }}
    .footer {{ background:#F8FAFC; border-top:1px solid #E2E8F0; padding:20px 32px;
               text-align:center; font-size:11px; color:#94A3B8; }}
    .badge {{ display:inline-block; background:#D1FAE5; color:#065F46; font-size:11px;
              font-weight:700; padding:4px 12px; border-radius:99px; border:1px solid #6EE7B7;
              text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="hero">
      <div class="hero-icon">🎉</div>
      <h1 class="hero-title">Félicitations, {nom_candidat} !</h1>
      <div class="hero-sub">Votre candidature a été sélectionnée</div>
    </div>
    <div class="body">
      <div style="text-align:center; margin-bottom:20px;">
        <span class="badge">✅ Candidat Retenu · Embauche Confirmée</span>
      </div>
      {score_section}
      <div class="greeting">
        <p>Cher(e) <strong>{nom_candidat}</strong>,</p>
        <p>Nous avons l'immense plaisir de vous informer que votre candidature pour le poste de
           <strong>{titre_offre}</strong> chez <strong>{agence}</strong> a été officiellement
           <strong style="color:#059669;">acceptée et confirmée</strong>.</p>
        <p>Notre équipe a soigneusement évalué votre profil via notre moteur d'intelligence artificielle
           et votre parcours correspond parfaitement à nos attentes.</p>
      </div>

      <div class="details-box">
        <div class="detail-row">
          <span class="detail-label">📋 Poste :</span>
          <span>{titre_offre}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">🏢 Entreprise :</span>
          <span>{agence}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">📍 Lieu :</span>
          <span>Fès, Maroc</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">🚀 Statut :</span>
          <span><strong>Embauche confirmée — En attente de contrat</strong></span>
        </div>
      </div>

      {note_section}

      <div class="steps">
        <div style="font-size:13px; font-weight:700; color:#64748B; text-transform:uppercase;
             letter-spacing:1px; margin-bottom:14px;">Prochaines étapes :</div>
        <div class="step">
          <div class="step-num">1</div>
          <div class="step-text">Notre équipe RH va vous contacter dans les <strong>48 heures</strong> pour planifier votre date de démarrage.</div>
        </div>
        <div class="step">
          <div class="step-num">2</div>
          <div class="step-text">Vous recevrez votre contrat de travail par e-mail pour signature.</div>
        </div>
        <div class="step">
          <div class="step-num">3</div>
          <div class="step-text">Préparez vos documents administratifs (CIN, diplômes, justificatif de domicile).</div>
        </div>
      </div>

      <p style="font-size:14px; color:#334155; line-height:1.65; margin-top:20px;">
        Nous sommes ravis de vous accueillir au sein de l'équipe <strong>{agence}</strong> et nous
        avons hâte de collaborer avec vous.<br><br>
        Cordialement,<br>
        <strong>L'Équipe Recrutement — {agence}</strong><br>
        <em style="font-size:12px; color:#94A3B8;">Powered by RecrutIA</em>
      </p>
    </div>
    <div class="footer">
      RecrutIA — Système Intelligent d'Automatisation &amp; Scoring du Recrutement &bull; {agence}
    </div>
  </div>
</body>
</html>"""
    return html


def envoyer_email_embauche(
    destinataire_email: str,
    nom_candidat: str,
    titre_offre: str,
    agence: str = "ArtiWeb Fès",
    note_rh: str = None,
    score_ia: float = None
) -> dict:
    """
    Envoie un email de confirmation d'embauche au candidat.
    Tente l'envoi SMTP réel si configuré, sinon simulation sécurisée.
    """
    cfg = get_smtp_config()
    html_content = generer_html_embauche(
        nom_candidat=nom_candidat,
        titre_offre=titre_offre,
        agence=agence,
        note_rh=note_rh,
        score_ia=score_ia
    )
    candidat_email = destinataire_email or "candidat@email.com"

    if cfg["host"] and cfg["user"] and cfg["pass"]:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🎉 Félicitations ! Votre embauche est confirmée — {titre_offre} ({agence})"
            msg["From"] = cfg["sender"] or cfg["user"]
            msg["To"] = candidat_email
            msg.attach(MIMEText(html_content, "html"))

            if cfg["port"] == 465:
                with smtplib.SMTP_SSL(cfg["host"], cfg["port"]) as server:
                    server.login(cfg["user"], cfg["pass"])
                    server.sendmail(cfg["sender"], [candidat_email], msg.as_string())
            else:
                with smtplib.SMTP(cfg["host"], cfg["port"]) as server:
                    server.starttls()
                    server.login(cfg["user"], cfg["pass"])
                    server.sendmail(cfg["sender"], [candidat_email], msg.as_string())

            logger.info(f"[Email Embauche] ✅ Email RÉEL envoyé à {candidat_email} (Offre: '{titre_offre}').")
            return {"statut": "envoye_smtp", "destinataire": candidat_email, "mode": f"SMTP Réel ({cfg['host']})"}
        except Exception as e:
            logger.error(f"[Email Embauche] Échec SMTP ({e}). Basculement sur le mode Démo.")

    logger.info(f"[Email Embauche Simulé] 🎉 Email embauche généré pour {candidat_email} (Offre: '{titre_offre}').")
    return {
        "statut": "envoye_demo",
        "destinataire": candidat_email,
        "mode": "Simulation Démo Réussie",
        "html_preview": html_content
    }
