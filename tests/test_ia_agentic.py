"""
Module : test_ia_agentic.py
Rôle   : Suite de tests unitaires et d'intégration de la Couche IA Agentique (Couche 2).

Exécution :
    python -m pytest tests/test_ia_agentic.py -v
"""

import sys
import unittest
from pathlib import Path

# Ajouter la racine au sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ia_agentic.evaluer_candidature import evaluer_candidature
from ia_agentic.hard_filter import verifier_criteres_durs
from ia_agentic.embeddings_scorer import calculer_score_semantique


# ════════════════════════════════════════════════════════════════
# Données de test synthétiques
# ════════════════════════════════════════════════════════════════

OFFRE_PYTHON_SENIOR = {
    "id": "OFFRE_PYTHON",
    "titre": "Développeur Senior Backend Python / Django",
    "experience_min_annees": 3,
    "competences_obligatoires": ["Python", "Django"],
    "competences_souhaitees": ["PostgreSQL", "Docker", "REST API", "Git"],
    "description": "Poste de développement d'API REST robustes avec Python, Django, PostgreSQL et Docker."
}

OFFRE_DEVOPS_EXPERT = {
    "id": "OFFRE_DEVOPS",
    "titre": "Expert DevOps & Kubernetes Senior",
    "experience_min_annees": 5,
    "competences_obligatoires": ["Kubernetes", "AWS"],
    "competences_souhaitees": ["Docker", "Linux", "CI/CD"],
    "description": "Poste d'architecte infrastructure Cloud Kubernetes et AWS."
}

CANDIDAT_BON_MATCH_PYTHON = {
    "fichier": "cv_ahmed_python_senior.pdf",
    "formation": "Master / Ingénieur",
    "experience_annees": 4,
    "competences": ["Python", "Django", "PostgreSQL", "Docker", "REST API", "Git", "Linux"],
    "texte_brut": "Développeur Python avec 4 ans d'expérience en création d'applications web Django et API REST."
}

CANDIDAT_JUNIOR_REJETE = {
    "fichier": "cv_yassine_junior.pdf",
    "formation": "Licence / Bachelor",
    "experience_annees": 1,  # Insuffisant pour poste exigeant 3 ou 5 ans
    "competences": ["HTML", "CSS", "JavaScript", "PHP"],  # Ne possède ni Python ni Django
    "texte_brut": "Développeur web junior spécialisé en création de sites vitrines HTML CSS PHP."
}

CANDIDAT_MOYEN_MATCH = {
    "fichier": "cv_fatima_data_ai.pdf",
    "formation": "Master / Ingénieur",
    "experience_annees": 3,  # Expérience suffisante
    "competences": ["Python", "Django", "Machine Learning", "Pandas", "Scikit-learn"],  # A Python et Django, mais pas Docker/Postgres
    "texte_brut": "Ingénieure IA travaillant en Python et Django pour intégrer des modèles ML."
}


# ════════════════════════════════════════════════════════════════
# Tests Unitaires du Filtre Dur (hard_filter)
# ════════════════════════════════════════════════════════════════

class TestHardFilter(unittest.TestCase):

    def test_candidat_valide_criteres_durs(self):
        valide, raison = verifier_criteres_durs(CANDIDAT_BON_MATCH_PYTHON, OFFRE_PYTHON_SENIOR)
        self.assertTrue(valide)

    def test_candidat_rejete_experience_insuffisante(self):
        # 1 an d'exp vs 5 ans exigés
        valide, raison = verifier_criteres_durs(CANDIDAT_JUNIOR_REJETE, OFFRE_DEVOPS_EXPERT)
        self.assertFalse(valide)
        self.assertIn("Expérience insuffisante", raison)

    def test_candidat_rejete_competences_obligatoires_manquantes(self):
        # Le junior n'a ni Python ni Django
        valide, raison = verifier_criteres_durs(CANDIDAT_JUNIOR_REJETE, OFFRE_PYTHON_SENIOR)
        self.assertFalse(valide)


# ════════════════════════════════════════════════════════════════
# Tests du Scoring Sémantique (embeddings_scorer)
# ════════════════════════════════════════════════════════════════

class TestEmbeddingsScorer(unittest.TestCase):

    def test_score_bon_match_superieur_score_moyen(self):
        score_bon, details_bon = calculer_score_semantique(CANDIDAT_BON_MATCH_PYTHON, OFFRE_PYTHON_SENIOR)
        score_moyen, details_moyen = calculer_score_semantique(CANDIDAT_MOYEN_MATCH, OFFRE_PYTHON_SENIOR)

        print(f"\n[Scoring Test] Score Bon Match: {score_bon} | Score Moyen Match: {score_moyen}")
        self.assertGreater(score_bon, score_moyen)
        self.assertGreaterEqual(score_bon, 70.0)


# ════════════════════════════════════════════════════════════════
# Tests d'Intégration — Pipeline evaluer_candidature()
# ════════════════════════════════════════════════════════════════

class TestIntegrationEvaluerCandidature(unittest.TestCase):

    def test_scenario_1_bon_match(self):
        """Scénario 1 — Bon match : profil adapté, score élevé, justification générée."""
        resultat = evaluer_candidature(CANDIDAT_BON_MATCH_PYTHON, OFFRE_PYTHON_SENIOR)

        self.assertEqual(resultat["statut"], "score")
        self.assertGreaterEqual(resultat["score"], 70.0)
        self.assertIn("Python", resultat["justification"])
        self.assertTrue("ÉVALUATION" in resultat["justification"] or "Appréciation" in resultat["justification"] or "score" in resultat["justification"].lower())

        print("\n" + "=" * 60)
        print("SCÉNARIO 1 — BON MATCH")
        print("=" * 60)
        print(f"Statut       : {resultat['statut']}")
        print(f"Score        : {resultat['score']}/100")
        print(f"Justification:\n{resultat['justification'][:250]}...")

    def test_scenario_2_rejet_automatique_filtre_dur(self):
        """Scénario 2 — Rejet automatique : critères durs non atteints, score=0.0, rejet immédiat."""
        resultat = evaluer_candidature(CANDIDAT_JUNIOR_REJETE, OFFRE_DEVOPS_EXPERT)

        self.assertEqual(resultat["statut"], "rejete_auto_filtre")
        self.assertEqual(resultat["score"], 0.0)
        self.assertIn("REJETÉE", resultat["justification"])

        print("\n" + "=" * 60)
        print("SCÉNARIO 2 — REJET AUTOMATIQUE CRITÈRES DURS")
        print("=" * 60)
        print(f"Statut       : {resultat['statut']}")
        print(f"Score        : {resultat['score']}/100")
        print(f"Motif        : {resultat['details']['motif_rejet']}")

    def test_scenario_3_cas_limite_match_modere(self):
        """Scénario 3 — Cas limite / match modéré : critères durs ok mais score intermédiaire."""
        resultat = evaluer_candidature(CANDIDAT_MOYEN_MATCH, OFFRE_PYTHON_SENIOR)

        self.assertEqual(resultat["statut"], "score")
        self.assertGreater(resultat["score"], 40.0)
        self.assertLess(resultat["score"], 85.0)

        print("\n" + "=" * 60)
        print("SCÉNARIO 3 — CAS LIMITE / MATCH MODÉRÉ")
        print("=" * 60)
        print(f"Statut       : {resultat['statut']}")
        print(f"Score        : {resultat['score']}/100")
        print(f"Justification:\n{resultat['justification'][:250]}...")


if __name__ == "__main__":
    unittest.main(verbosity=2)
