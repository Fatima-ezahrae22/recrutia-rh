"""
Package : ingestion
Description : Couche d'ingestion de l'Agent IA RH.
              Transforme des fichiers CV bruts (PDF/DOCX) en données structurées JSON.
"""

from ingestion.traiter_cv import traiter_cv

__all__ = ["traiter_cv"]
__version__ = "1.0.0"
