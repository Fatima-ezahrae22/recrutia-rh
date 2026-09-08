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
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

logger = logging.getLogger("RecrutIA.Email")

def get_smtp_config():
    user = os.environ.get("SMTP_USER", "").strip()
    return {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com").strip(),
        "port": int(os.environ.get("SMTP_PORT", 587)),
        "user": user,
        "pass": os.environ.get("SMTP_PASS", "").strip(),
        "sender": os.environ.get("SENDER_EMAIL", user or "recrutement@artiweb.ma").strip()
    }


def generer_html_convocation(
    nom_candidat: str,
    titre_offre: str,
    date_heure: str,
    format_entretien: str,
    lieu_ou_lien: str,
    message_personnalise: str = None
) -> str:
    """Génère le modèle d'email HTML professionnel de convocation assorti au thème RecrutIA."""
    type_format = "en nos locaux à Fès" if format_entretien.upper() == "PRESENTIEL" else "en visioconférence (Google Meet)"

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #E2E8F0; background-color: #090D16; padding: 24px; margin: 0; }}
    .card {{ background-color: #0F172A; border: 1px solid #312E81; border-radius: 20px; max-width: 620px; margin: 0 auto; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(79, 70, 229, 0.25); }}
    .hero {{ background: linear-gradient(135deg, #312E81 0%, #4F46E5 50%, #D97706 100%); padding: 36px 32px; text-align: center; border-bottom: 2px solid #F59E0B; }}
    .hero-brand {{ font-size: 11px; font-weight: 900; color: #F59E0B; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 6px; }}
    .hero-title {{ color: #FFFFFF; font-size: 24px; font-weight: 900; margin: 0; text-shadow: 0 2px 10px rgba(0,0,0,0.3); }}
    .body {{ padding: 32px; }}
    .greeting {{ font-size: 15px; line-height: 1.7; color: #CBD5E1; margin-bottom: 20px; }}
    .details-box {{ background: #1E1B4B; border: 1px solid #6366F1; border-left: 5px solid #F59E0B; border-radius: 14px; padding: 20px; margin: 24px 0; }}
    .detail-row {{ font-size: 14px; margin-bottom: 10px; color: #E2E8F0; }}
    .detail-row:last-child {{ margin-bottom: 0; }}
    .detail-row strong {{ color: #F59E0B; }}
    .msg-rh {{ background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 14px 18px; margin: 18px 0; font-size: 13px; color: #FDE68A; font-style: italic; }}
    .footer {{ background-color: #05070E; border-top: 1px solid #1E1B4B; padding: 20px 32px; text-align: center; font-size: 11px; color: #64748B; }}
    .badge {{ display: inline-block; background: rgba(245, 158, 11, 0.2); color: #F59E0B; font-size: 11px; font-weight: 800; padding: 5px 14px; border-radius: 99px; border: 1px solid #F59E0B; text-transform: uppercase; letter-spacing: 1px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="hero">
      <div class="hero-brand">✨ RECRUTIA RH &bull; ARTIWEB FÈS</div>
      <h1 class="hero-title">Convocation à votre Entretien</h1>
    </div>
    <div class="body">
      <div style="text-align: center; margin-bottom: 20px;">
        <span class="badge">📅 Entretien RH Programmé</span>
      </div>
      <div class="greeting">
        <p>Bonjour <strong style="color:#FFF;">{nom_candidat}</strong>,</p>
        <p>Suite à l'analyse sémantique de votre candidature par notre moteur d'Intelligence Artificielle pour le poste de <strong style="color:#818CF8;">{titre_offre}</strong>, nous avons le plaisir de vous confirmer votre sélection pour l'étape d'entretien.</p>
      </div>

      <div class="details-box">
        <div class="detail-row">📅 <strong>Date & Heure :</strong> <span style="color:#FFF;">{date_heure}</span></div>
        <div class="detail-row">📍 <strong>Format :</strong> <span style="color:#FFF;">Entretien {type_format}</span></div>
        <div class="detail-row">🗺️ <strong>Lieu / Lien :</strong> <span style="color:#FFF;">{lieu_ou_lien}</span></div>
      </div>

      {f'<div class="msg-rh">💬 <strong>Message de l\'Équipe RH :</strong><br>{message_personnalise}</div>' if message_personnalise else ""}

      <p style="font-size: 13.5px; color: #94A3B8; line-height: 1.6; margin-top: 24px;">
        Merci de bien vouloir nous confirmer votre disponibilité en répondant à cet e-mail.<br><br>
        Cordialement,<br>
        <strong style="color:#FFF;">L'Équipe RH — ArtiWeb Fès</strong><br>
        <em style="font-size: 11px; color: #64748B;">Plateforme d'Évaluation & Scoring IA RecrutIA</em>
      </p>
    </div>
    <div class="footer">
      RecrutIA &bull; Système Intelligent d'Automatisation & Scoring du Recrutement &bull; ArtiWeb Fès
    </div>
  </div>
</body>
</html>"""
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
    """Génère un email HTML professionnel d'embauche aux couleurs de la plateforme candidat RecrutIA."""
    score_section = ""
    if score_ia is not None:
        score_section = f"""
        <div style="text-align:center; margin: 20px 0;">
          <div style="display:inline-block; background:linear-gradient(135deg, #10B981, #059669);
               color:#fff; border-radius:50%; width:86px; height:86px;
               line-height:86px; font-size:26px; font-weight:900; font-family:sans-serif; box-shadow:0 0 25px rgba(16,185,129,0.4); border:2px solid #6EE7B7;">
            {round(score_ia)}%
          </div>
          <div style="font-size:11px; color:#10B981; margin-top:8px; font-weight:800; text-transform:uppercase; letter-spacing:1px;">
            Score d'Adéquation IA Validé
          </div>
        </div>"""

    note_section = ""
    if note_rh:
        note_section = f"""
        <div style="background:rgba(16,185,129,0.1); border-left:4px solid #10B981; border-radius:0 12px 12px 0;
             padding:16px 20px; margin:20px 0; font-size:13.5px; color:#A7F3D0; font-style:italic;">
          <strong style="color:#10B981;">Note de l'Équipe RH :</strong><br>{note_rh}
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif; color:#E2E8F0; background:#090D16; padding:24px; margin:0; }}
    .card {{ background:#0F172A; border:1px solid #047857; border-radius:20px; max-width:620px;
             margin:0 auto; overflow:hidden; box-shadow:0 25px 50px -12px rgba(16,185,129,0.25); }}
    .hero {{ background:linear-gradient(135deg,#047857 0%,#10B981 50%,#D97706 100%); padding:40px 32px; text-align:center; border-bottom:2px solid #10B981; }}
    .hero-icon {{ font-size:48px; margin-bottom:12px; }}
    .hero-title {{ color:#FFFFFF; font-size:26px; font-weight:900; margin:0; text-shadow:0 2px 10px rgba(0,0,0,0.3); }}
    .hero-sub {{ color:rgba(255,255,255,0.9); font-size:14px; margin-top:6px; font-weight:600; }}
    .body {{ padding:32px; }}
    .greeting {{ font-size:15px; line-height:1.7; color:#CBD5E1; margin-bottom:20px; }}
    .details-box {{ background:#1E1B4B; border:1px solid #10B981; border-radius:14px; padding:20px; margin:24px 0; }}
    .detail-row {{ font-size:14px; margin-bottom:10px; color:#E2E8F0; }}
    .detail-row:last-child {{ margin-bottom:0; }}
    .detail-label {{ font-weight:700; color:#10B981; min-width:110px; display:inline-block; }}
    .steps {{ margin:24px 0; }}
    .step {{ display:flex; gap:14px; margin-bottom:16px; align-items:flex-start; }}
    .step-num {{ background:linear-gradient(135deg,#10B981,#059669); color:#fff; border-radius:50%;
                 width:28px; height:28px; min-width:28px; display:flex; align-items:center;
                 justify-content:center; font-size:12px; font-weight:900; shadow:0 4px 10px rgba(16,185,129,0.3); }}
    .step-text {{ font-size:13.5px; line-height:1.55; color:#CBD5E1; padding-top:4px; }}
    .footer {{ background:#05070E; border-top:1px solid #1E1B4B; padding:20px 32px;
               text-align:center; font-size:11px; color:#64748B; }}
    .badge {{ display:inline-block; background:rgba(16,185,129,0.2); color:#10B981; font-size:11px;
              font-weight:800; padding:5px 14px; border-radius:99px; border:1px solid #10B981;
              text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="hero">
      <div class="hero-icon">🎉</div>
      <h1 class="hero-title">Félicitations, {nom_candidat} !</h1>
      <div class="hero-sub">Votre recrutement chez {agence} est officiel</div>
    </div>
    <div class="body">
      <div style="text-align:center; margin-bottom:20px;">
        <span class="badge">✅ Candidature Retenue &bull; Embauche Confirmée</span>
      </div>
      {score_section}
      <div class="greeting">
        <p>Cher(e) <strong style="color:#FFF;">{nom_candidat}</strong>,</p>
        <p>Nous avons le grand plaisir de vous informer que suite aux étapes d'évaluation et d'entretien, votre candidature pour le poste de
           <strong style="color:#10B981;">{titre_offre}</strong> chez <strong style="color:#FFF;">{agence}</strong> a été officiellement
           <strong style="color:#10B981;">retenue et validée par la direction RH</strong>.</p>
      </div>

      <div class="details-box">
        <div class="detail-row">
          <span class="detail-label">📋 Poste :</span>
          <span style="color:#FFF; font-weight:700;">{titre_offre}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">🏢 Entreprise :</span>
          <span style="color:#FFF;">{agence}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">📍 Localisation :</span>
          <span style="color:#FFF;">Fès, Maroc</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">🚀 Statut :</span>
          <span style="color:#10B981; font-weight:700;">Embauche confirmée &bull; Dossier Validé</span>
        </div>
      </div>

      {note_section}

      <div class="steps">
        <div style="font-size:12px; font-weight:800; color:#818CF8; text-transform:uppercase;
             letter-spacing:1px; margin-bottom:14px;">Prochaines étapes de votre intégration :</div>
        <div class="step">
          <div class="step-num">1</div>
          <div class="step-text">Notre responsable RH va vous contacter sous <strong>48 heures</strong> pour convenir de votre date exacte de prise de poste.</div>
        </div>
        <div class="step">
          <div class="step-num">2</div>
          <div class="step-text">Votre contrat de travail vous sera transmis par voie électronique pour signature.</div>
        </div>
        <div class="step">
          <div class="step-num">3</div>
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
