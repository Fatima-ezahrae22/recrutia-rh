"""
Module : routers/auth.py
Rôle   : Endpoints d'authentification JWT (Inscription, Connexion, Profil).
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas import UserCreate, UserLogin, Token, UserResponse
from backend.auth import (
    hash_password, verify_password,
    creer_access_token, get_current_user
)

logger = logging.getLogger("RecrutIA.AuthRouter")

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Inscription d'un nouveau compte recruteur ou administrateur."""
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris.")
    role_choisi = user_in.role if user_in.role in ["recruteur", "admin"] else "recruteur"
    user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        role=role_choisi
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"[Auth] Nouveau compte créé ({role_choisi}) : {user.username}")
    return user


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """Connexion et génération d'un token JWT."""
    user = db.query(User).filter(User.username == user_in.username).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect."
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé.")
    token = creer_access_token(data={"sub": user.username, "role": user.role})
    logger.info(f"[Auth] Connexion réussie : {user.username}")
    return Token(access_token=token, token_type="bearer", username=user.username, role=user.role)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retourne les informations de l'utilisateur connecté."""
    return current_user


@router.get("/users", response_model=List[UserResponse])
def lister_utilisateurs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Permet à l'Administrateur de lister tous les comptes de la plateforme."""
    if current_user.role != "admin":
        # Seul un admin peut voir tous les comptes, sinon retourne une liste limitée
        return [current_user]
    return db.query(User).order_by(User.created_at.desc()).all()


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def supprimer_utilisateur(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Permet à un Admin de supprimer un compte utilisateur."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Seul un Administrateur peut supprimer des comptes.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
    if user.username == current_user.username:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte.")
    db.delete(user)
    db.commit()
    logger.info(f"[Auth] Compte {user.username} supprimé par l'admin {current_user.username}")
    return {"message": f"Le compte '{user.username}' a été supprimé avec succès."}
