"""
Module : test_backend.py
Rôle   : Suite de tests d'intégration d'API REST pour le Backend FastAPI (Tâche 3).

Exécution :
    python -m pytest tests/test_backend.py -v
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

# Ajouter la racine au sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.main import app
from backend.database import Base, engine

client = TestClient(app)


def _creer_pdf_temp(texte: str) -> str:
    """Helper pour créer un PDF temporaire propre compatible Windows."""
    import fitz
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), texte, fontsize=10)
    doc.save(path)
    doc.close()
    return path


class TestBackendAPI(unittest.TestCase):

    def setUp(self):
        """Réinitialise la base de données avant chaque test."""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_01_health_check(self):
        """Vérifie l'endpoint racine GET /."""
        response = client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_02_creer_offre(self):
        """Vérifie la création d'une offre via POST /api/offres."""
        payload = {
            "titre": "Développeur Python Senior Backend",
            "description": "Développement d'API REST robustes avec FastAPI et PostgreSQL.",
            "experience_min_annees": 3,
            "competences_obligatoires": ["Python", "Django"],
            "competences_souhaitees": ["Docker", "PostgreSQL", "FastAPI"],
            "formation_exigee": "Master / Ingénieur"
        }
        response = client.post("/api/offres", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["titre"], payload["titre"])
        self.assertIn("id", data)

    def test_03_lister_offres(self):
        """Vérifie le listing des offres via GET /api/offres."""
        client.post("/api/offres", json={
            "titre": "Offre Test",
            "description": "Description Test",
            "experience_min_annees": 1
        })
        response = client.get("/api/offres")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 1)

    def test_04_soumettre_candidature_et_pipeline(self):
        """Vérifie la soumission d'un CV et l'exécution du pipeline complet (Ingestion ➔ IA ➔ DB)."""
        # 1. Créer une offre
        res_offre = client.post("/api/offres", json={
            "titre": "Développeur Python Senior Backend",
            "description": "Développement d'API REST avec Python et FastAPI.",
            "experience_min_annees": 3,
            "competences_obligatoires": ["Python", "Django"],
            "competences_souhaitees": ["Docker", "PostgreSQL"]
        })
        offre_id = res_offre.json()["id"]

        # 2. Créer un PDF textuel
        cv_text = """\
Ahmed BENNANI
Email : ahmed.bennani@email.ma
Tel : +212 6 61 23 45 67
FORMATION
Ingénieur en Génie Informatique, École Mohammadia d'Ingénieurs (2018 - 2023)
EXPÉRIENCE PROFESSIONNELLE
Développeur Python Senior — TechCorp Maroc (2020 - 2024)
- Développement backend avec Python, Django, FastAPI et PostgreSQL.
- Conteneurisation avec Docker et intégration CI/CD avec Git.
COMPÉTENCES
Python, Django, FastAPI, PostgreSQL, Docker, Git, REST API
"""
        tmp_path = _creer_pdf_temp(cv_text)

        with open(tmp_path, "rb") as f:
            response = client.post(
                "/api/candidatures",
                data={"offre_id": str(offre_id)},
                files={"fichier_cv": ("cv_ahmed.pdf", f, "application/pdf")}
            )

        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["statut_ingestion"], "succès")
        self.assertEqual(data["statut_ia"], "score")
        self.assertGreaterEqual(data["score"], 70.0)

    def test_05_lister_candidatures_triees(self):
        """Vérifie la consultation des candidatures triées par score décroissant via GET /api/offres/{id}/candidatures."""
        # 1. Créer une offre
        res_offre = client.post("/api/offres", json={
            "titre": "Ingénieur Data",
            "description": "Poste Data",
            "experience_min_annees": 1
        })
        offre_id = res_offre.json()["id"]

        # 2. Soumettre un CV
        cv_text = "Fatima ZAHRA\nEmail: fatima@email.ma\nMaster Informatique (2021-2023)\nExpérience Data: 2 ans (2022-2024)\nCompétences: Python, SQL, Pandas."
        tmp_path = _creer_pdf_temp(cv_text)

        with open(tmp_path, "rb") as f:
            client.post("/api/candidatures", data={"offre_id": str(offre_id)}, files={"fichier_cv": ("cv_fatima.pdf", f, "application/pdf")})

        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        response = client.get(f"/api/offres/{offre_id}/candidatures")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)

    def test_06_enregistrer_decision_rh(self):
        """Vérifie l'enregistrement de la décision RH via PATCH /api/candidatures/{id}/decision."""
        # 1. Offre
        res_offre = client.post("/api/offres", json={"titre": "Offre RH", "description": "Desc"})
        offre_id = res_offre.json()["id"]

        # 2. Candidature
        cv_text = "Youssef AMRANI\nEmail: youssef@email.ma\nIngénieur 3 ans\nCompétences: Python, Django."
        tmp_path = _creer_pdf_temp(cv_text)

        with open(tmp_path, "rb") as f:
            res_cand = client.post("/api/candidatures", data={"offre_id": str(offre_id)}, files={"fichier_cv": ("cv_youssef.pdf", f, "application/pdf")})

        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        cand_id = res_cand.json()["id"]

        # 3. Décision RH
        payload = {
            "decision": "VALIDE",
            "note_rh": "Profil excellent présélectionné pour entretien technique.",
            "rh_utilisateur": "Responsable RH ArtiWeb"
        }
        response = client.patch(f"/api/candidatures/{cand_id}/decision", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["decision_rh"], "VALIDE")

    def test_07_consulter_audit_log(self):
        """Vérifie la présence des logs d'audit via GET /api/audit."""
        client.post("/api/offres", json={"titre": "Offre Audit Test", "description": "Desc"})
        response = client.get("/api/audit")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
