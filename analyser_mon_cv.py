# -*- coding: utf-8 -*-
"""
analyser_mon_cv.py (Version Améliorée)
-------------------------------------
Détecte automatiquement TOUS les CV (PDF/DOCX) dans le dossier mes_cv/
quelle que soit la casse des extensions (.pdf, .PDF, .docx, .DOCX).
"""

import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, ".")

import logging
logging.disable(logging.CRITICAL)

from ingestion.traiter_cv import traiter_cv

DOSSIER_CV = "mes_cv"

# ─── 1. S'assurer que le dossier existe ───────────────────
if not os.path.exists(DOSSIER_CV):
    os.makedirs(DOSSIER_CV)

# ─── 2. Trouver TOUS les CV dans le dossier (PDF / DOCX) ────
fichiers = [
    f for f in os.listdir(DOSSIER_CV)
    if f.lower().endswith((".pdf", ".docx")) and not f.endswith("_resultat.json")
]

print()
print("╔══════════════════════════════════════════════════════╗")
print("║        AGENT IA RH  —  Analyse de CV                ║")
print("╚══════════════════════════════════════════════════════╝")
print()

# ─── Aucun CV trouvé ───────────────────────────────────────
if not fichiers:
    print("  ⚠️  Aucun CV trouvé dans le dossier  mes_cv/")
    print()
    print("  --> Copiez vos CV (.pdf ou .docx) dans :")
    print(f"      {os.path.abspath(DOSSIER_CV)}")
    print()
    print("  --> Puis relancez :  python -X utf8 analyser_mon_cv.py")
    print()
    sys.exit()

# ─── Afficher la liste complète des CV disponibles ─────────
print(f"  📂 {len(fichiers)} CV disponible(s) dans le dossier mes_cv/ :\n")
for i, f in enumerate(fichiers, 1):
    print(f"    [{i}]  {f}")
print()

# ─── Choix du CV à analyser ─────────────────────────────────
if len(fichiers) == 1:
    choix = 1
    print(f"  -> Analyse automatique du seul CV trouvé : {fichiers[0]}")
else:
    try:
        saisie = input(f"  Entrez le numéro du CV à analyser (1 à {len(fichiers)}) : ")
        choix = int(saisie.strip())
        if choix < 1 or choix > len(fichiers):
            raise ValueError
    except (ValueError, KeyboardInterrupt):
        print("\n  ❌ Numéro invalide ou annulation. Arrêt du programme.")
        sys.exit()

nom_fichier = fichiers[choix - 1]
chemin_cv   = os.path.join(DOSSIER_CV, nom_fichier)

print()
print(f"  ⏳  Traitement de  '{nom_fichier}'  en cours...")
print()

# ─── Lancer le pipeline traiter_cv ─────────────────────────
resultat = traiter_cv(chemin_cv)

# ─── Affichage du résultat ─────────────────────────────────
print("╔══════════════════════════════════════════════════════╗")
print("║                   RÉSULTAT FINAL                    ║")
print("╚══════════════════════════════════════════════════════╝")
print()

if resultat["statut"] == "succès":
    print(f"  ✅  Statut           : SUCCÈS")
    print(f"  🎓  Formation        : {resultat['formation']}")
    print(f"  📅  Expérience       : {resultat['experience_annees']} an(s)")
    print(f"  ⏱️   Durée traitement : {resultat['duree_traitement']} s")
    print()

    comps = resultat["competences"]
    print(f"  🛠️  {len(comps)} Compétence(s) détectée(s) :")
    for i in range(0, len(comps), 4):
        ligne = comps[i:i+4]
        print("      " + "  |  ".join(f"{c:<18}" for c in ligne))

    print()
    print("  📝  Aperçu du texte extrait :")
    print("  " + "─" * 52)
    apercu = resultat["texte_brut"][:350].replace("\n", "\n  ")
    print(f"  {apercu}...")
    print("  " + "─" * 52)
    print()

    # Sauvegarder le résultat JSON
    nom_base = os.path.splitext(nom_fichier)[0]
    nom_sortie = f"{nom_base}_resultat.json"
    chemin_sortie = os.path.join(DOSSIER_CV, nom_sortie)
    with open(chemin_sortie, "w", encoding="utf-8") as f:
        json.dump(resultat, f, ensure_ascii=False, indent=4)

    print(f"  💾  Résultat JSON sauvegardé dans : mes_cv/{nom_sortie}")

else:
    print(f"  ❌  Erreur : {resultat['message']}")

print()
print("══════════════════════════════════════════════════════")
print()
