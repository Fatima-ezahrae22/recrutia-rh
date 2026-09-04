"""
Script : test_email.py
Role   : Script de test independant pour verifier l'envoi d'emails reels avec les variables du fichier .env
"""

import os
import sys
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Forcer l'encodage UTF-8 sur Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Charger les variables du fichier .env
load_dotenv()

def envoyer_email(destinataire, sujet, corps):
    host = os.environ.get("SMTP_HOST", "")
    port = int(os.environ.get("SMTP_PORT", 587))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASS", "")
    sender = os.environ.get("SENDER_EMAIL", user)

    if not host or not user or not password:
        print("ERREUR : Les variables SMTP_HOST, SMTP_USER ou SMTP_PASS sont vides dans le fichier .env !")
        return

    msg = EmailMessage()
    msg["Subject"] = sujet
    msg["From"] = sender
    msg["To"] = destinataire
    msg.set_content(corps)

    print(f"[SMTP] Connexion a {host}:{port} avec {user}...")

    try:
        if port == 465:
            # Mode SSL (Port 465)
            with smtplib.SMTP_SSL(host, port) as smtp:
                smtp.login(user, password)
                smtp.send_message(msg)
        else:
            # Mode STARTTLS (Port 587 ou 25)
            with smtplib.SMTP(host, port) as smtp:
                smtp.starttls()
                smtp.login(user, password)
                smtp.send_message(msg)
        print("[SUCCES] Email envoye avec succes !")
    except Exception as e:
        print(f"[ECHEC] Erreur lors de l'envoi : {e}")

if __name__ == "__main__":
    dest = input("Adresse email destinataire pour le test : ").strip()
    if dest:
        envoyer_email(dest, "Test Agent IA RH - RecrutIA", "Ceci est un e-mail de test envoye depuis RecrutIA.")