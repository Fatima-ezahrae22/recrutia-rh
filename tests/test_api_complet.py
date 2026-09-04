"""
Script de test complet des fonctionnalités de l'API RecrutIA (unittest).
"""

import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine

client = TestClient(app)

class TestRecrutIA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def test_01_auth(self):
        res_reg = client.post("/api/auth/register", json={
            "username": "test_rh_user",
            "password": "Password123!"
        })
        self.assertIn(res_reg.status_code, [201, 400])

        res_login = client.post("/api/auth/login", json={
            "username": "recruteur",
            "password": "RecrutIA2026!"
        })
        self.assertEqual(res_login.status_code, 200)
        token_data = res_login.json()
        self.assertIn("access_token", token_data)
        return token_data["access_token"]

    def test_02_offres(self):
        token = self.test_01_auth()
        headers = {"Authorization": f"Bearer {token}"}

        res_create = client.post("/api/offres", json={
            "titre": "Développeur Python Fullstack Test",
            "description": "Poste de test automatisé pour validation du système RecrutIA.",
            "experience_min_annees": 2,
            "competences_obligatoires": ["Python", "FastAPI", "SQL"],
            "competences_souhaitees": ["Docker", "Vue.js"],
            "formation_exigee": "Bac+5 Informatique"
        }, headers=headers)
        self.assertEqual(res_create.status_code, 201)
        offre_id = res_create.json()["id"]

        res_list_rh = client.get("/api/offres", headers=headers)
        self.assertEqual(res_list_rh.status_code, 200)
        self.assertGreater(len(res_list_rh.json()), 0)

        res_list_pub = client.get("/api/public/offres")
        self.assertEqual(res_list_pub.status_code, 200)
        self.assertGreater(len(res_list_pub.json()), 0)

        return offre_id, token

    def test_03_candidatures_publiques_et_rh(self):
        offre_id, token = self.test_02_offres()
        headers = {"Authorization": f"Bearer {token}"}

        cv_content = b"%PDF-1.4 Mock CV Content with Python FastAPI experience"
        files = {"fichier_cv": ("cv_candidat_test.pdf", cv_content, "application/pdf")}
        data = {
            "offre_id": str(offre_id),
            "nom_candidat": "Jean Candidat",
            "email_candidat": "jean.candidat@example.com"
        }

        res_pub_cand = client.post("/api/public/candidatures", data=data, files=files)
        self.assertEqual(res_pub_cand.status_code, 201)
        candidature_data = res_pub_cand.json()
        self.assertIn("score", candidature_data)
        candidature_id = candidature_data["id"]

        res_get_cand = client.get(f"/api/candidatures/{candidature_id}", headers=headers)
        self.assertEqual(res_get_cand.status_code, 200)
        self.assertEqual(res_get_cand.json()["candidat"]["nom"], "Jean Candidat")

        res_dec = client.patch(f"/api/candidatures/{candidature_id}/decision", json={
            "decision": "VALIDE",
            "note_rh": "Très bon profil retenu pour entretien."
        }, headers=headers)
        self.assertEqual(res_dec.status_code, 200)
        self.assertEqual(res_dec.json()["decision_rh"], "VALIDE")

        res_conv = client.post(f"/api/candidatures/{candidature_id}/convocation", json={
            "date_heure": "Demain à 14h00",
            "format_entretien": "VISIO",
            "lieu_ou_lien": "https://meet.google.com/test-recrutia",
            "message_personnalise": "Merci d'être ponctuel."
        }, headers=headers)
        self.assertEqual(res_conv.status_code, 200)
        self.assertEqual(res_conv.json()["statut"], "succes")

    def test_04_audit_et_entretiens(self):
        token = self.test_01_auth()
        headers = {"Authorization": f"Bearer {token}"}

        res_audit = client.get("/api/audit", headers=headers)
        self.assertEqual(res_audit.status_code, 200)
        self.assertIsInstance(res_audit.json(), list)

        res_entretiens = client.get("/api/entretiens", headers=headers)
        self.assertEqual(res_entretiens.status_code, 200)
        self.assertIsInstance(res_entretiens.json(), list)

if __name__ == "__main__":
    unittest.main()
