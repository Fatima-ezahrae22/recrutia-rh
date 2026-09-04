"""
Module : auth.py
Rôle   : Gestion de l'authentification JWT (JSON Web Token) pour l'API RecrutIA.
         Fournit : hachage de mots de passe (bcrypt), génération de tokens JWT,
         dépendance FastAPI get_current_user avec vraie validation.
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

try:
    import jwt
except ImportError:
    import PyJWT as jwt

try:
    import bcrypt
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    def verify_password(plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
except ImportError:
    import hashlib
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    def verify_password(plain: str, hashed: str) -> bool:
        return hashlib.sha256(plain.encode()).hexdigest() == hashed

from backend.database import get_db

logger = logging.getLogger("RecrutIA.Auth")

# Configuration JWT
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "recrutia-secret-key-artiweb-2026-secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 heures

security = HTTPBearer(auto_error=False)


def creer_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Génère un token JWT signé avec les données fournies."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decoder_token(token: str) -> Optional[dict]:
    """Décode et valide un token JWT. Retourne None si invalide ou expiré."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("[Auth] Token JWT expiré.")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"[Auth] Token JWT invalide : {e}")
        return None


from fastapi import Request

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Dépendance FastAPI : Valide le token JWT et retourne l'utilisateur connecté.
    - Supporte le token dans l'en-tête 'Authorization: Bearer <token>' OU le paramètre d'URL '?token=<token>'.
    """
    from backend.models import User

    raw_token = None
    if credentials and credentials.credentials:
        raw_token = credentials.credentials
    elif token:
        raw_token = token
    elif request and request.query_params.get("token"):
        raw_token = request.query_params.get("token")

    if raw_token:
        payload = decoder_token(raw_token)
        if payload and payload.get("sub"):
            username = payload.get("sub")
            user = db.query(User).filter(User.username == username).first()
            if user and user.is_active:
                return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré. Veuillez vous reconnecter.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise. Veuillez vous connecter.",
        headers={"WWW-Authenticate": "Bearer"},
    )
