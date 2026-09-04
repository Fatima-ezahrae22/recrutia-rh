"""
Script : create_admin.py
Role   : Creer ou reinitialiser un compte administrateur pour RecrutIA RH.
Usage  : python create_admin.py
         Sans arguments -> mode interactif
         Avec arguments -> python create_admin.py --username admin --password MonMotDePasse
"""

import sys
import os
import io
import argparse

# Forcer UTF-8 pour le terminal Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ajouter le dossier racine au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import direct sans passer par backend/__init__.py (qui chargerait FastAPI)
from backend.database import SessionLocal, init_db
from backend.models import User

try:
    import bcrypt
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
except ImportError:
    import hashlib
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()


def creer_admin(username: str, password: str) -> None:
    """Cree ou met a jour un compte admin dans la base de donnees."""
    init_db()
    db = SessionLocal()
    try:
        user_existant = db.query(User).filter(User.username == username).first()
        hashed = hash_password(password)

        if user_existant:
            user_existant.hashed_password = hashed
            user_existant.role = "recruteur"
            user_existant.is_active = True
            db.commit()
            print(f"\n[OK] Compte '{username}' mis a jour avec succes (role : recruteur).")
        else:
            nouveau_user = User(
                username=username,
                hashed_password=hashed,
                role="recruteur",
                is_active=True
            )
            db.add(nouveau_user)
            db.commit()
            print(f"\n[OK] Compte recruteur '{username}' cree avec succes.")

        print(f"   -> Connectez-vous sur http://127.0.0.1:8000/rh")
        print(f"   -> Identifiants : {username} / [votre mot de passe]\n")

    except Exception as e:
        db.rollback()
        print(f"\n[ERREUR] Impossible de creer le compte : {e}")
        sys.exit(1)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Creer ou reinitialiser un compte administrateur RecrutIA RH"
    )
    parser.add_argument("--username", type=str, help="Nom d'utilisateur admin")
    parser.add_argument("--password", type=str, help="Mot de passe (min. 6 caracteres)")

    args = parser.parse_args()

    print("\n" + "=" * 55)
    print("   RecrutIA RH -- Creation de compte Administrateur")
    print("=" * 55)

    username = args.username
    password = args.password

    # Mode interactif si pas d'arguments
    if not username:
        username = input("\nNom d'utilisateur admin : ").strip()
    if not username:
        print("[ERREUR] Le nom d'utilisateur ne peut pas etre vide.")
        sys.exit(1)

    if not password:
        import getpass
        password = getpass.getpass(f"Mot de passe pour '{username}' (min. 6 car.) : ")
        confirm = getpass.getpass("Confirmer le mot de passe : ")
        if password != confirm:
            print("[ERREUR] Les mots de passe ne correspondent pas.")
            sys.exit(1)

    if len(password) < 6:
        print("[ERREUR] Le mot de passe doit contenir au moins 6 caracteres.")
        sys.exit(1)

    creer_admin(username, password)


if __name__ == "__main__":
    main()
