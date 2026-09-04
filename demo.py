"""
demo.py — Démonstration de la couche ingestion
Lancez : python demo.py
"""

import sys
import json
sys.path.insert(0, ".")   # s'assure que le projet est trouvé

from ingestion.traiter_cv import traiter_cv

# ─────────────────────────────────────────────────────────────
# Remplacez ce chemin par le chemin réel vers votre CV PDF/DOCX
# ─────────────────────────────────────────────────────────────
CHEMIN_CV = r"C:\chemin\vers\votre\cv.pdf"   # <-- à modifier

# ─────────────────────────────────────────────────────────────
# Traitement
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  Agent IA RH -- Couche Ingestion")
print("=" * 55)

resultat = traiter_cv(CHEMIN_CV)

# Affichage JSON propre (sans le texte brut pour lisibilité)
affichage = {
    "fichier"           : resultat["fichier"],
    "statut"            : resultat["statut"],
    "formation"         : resultat["formation"],
    "experience_annees" : resultat["experience_annees"],
    "competences"       : resultat["competences"],
    "message"           : resultat["message"],
    "duree_traitement"  : str(resultat["duree_traitement"]) + " s",
    "texte_brut_apercu" : resultat["texte_brut"][:300] + "..."
                          if len(resultat["texte_brut"]) > 300
                          else resultat["texte_brut"],
}

print("\nResultat JSON :")
print(json.dumps(affichage, ensure_ascii=False, indent=2))
