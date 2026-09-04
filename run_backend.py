# -*- coding: utf-8 -*-
"""
run_backend.py — Lance le serveur API REST FastAPI avec uvicorn
Commandes d'accès :
    - Swagger Documentation UI : http://127.0.0.1:8000/docs
    - Redoc Documentation UI   : http://127.0.0.1:8000/redoc
"""

import uvicorn
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print()
    print("======================================================================")
    print("         AGENT IA RH  --  SERVEUR API BACKEND FASTAPI                 ")
    print("======================================================================")
    print()
    print("  Serveur API demarre sur : http://127.0.0.1:8000")
    print("  Interface RH            : http://127.0.0.1:8000/rh")
    print("  Interface Candidat      : http://127.0.0.1:8000/candidat")
    print("  Interface Swagger UI    : http://127.0.0.1:8000/docs")
    print()

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
