"""
Script de migration de la base de données.
Ajoute les nouvelles colonnes sans recréer la DB.
"""
import sqlite3
import os

DB_PATH = "agent_rh.db"

if not os.path.exists(DB_PATH):
    print(f"Fichier DB introuvable : {DB_PATH}")
    exit(1)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 1. Ajouter cv_chemin_stocke dans candidats
cols_candidats = [r[1] for r in c.execute("PRAGMA table_info(candidats)").fetchall()]
if "cv_chemin_stocke" not in cols_candidats:
    c.execute("ALTER TABLE candidats ADD COLUMN cv_chemin_stocke TEXT")
    print("[OK] cv_chemin_stocke ajoute dans la table candidats")
else:
    print("[INFO] cv_chemin_stocke deja present dans candidats")

# 2. Ajouter statut dans candidatures
cols_cands = [r[1] for r in c.execute("PRAGMA table_info(candidatures)").fetchall()]
if "statut" not in cols_cands:
    c.execute("ALTER TABLE candidatures ADD COLUMN statut TEXT DEFAULT 'EN_ATTENTE'")
    # Synchroniser statut avec decision_rh existante
    c.execute("""
        UPDATE candidatures SET statut = CASE
            WHEN decision_rh = 'VALIDE' THEN 'ACCEPTE'
            WHEN decision_rh = 'REJETE' THEN 'REFUSE'
            ELSE 'EN_ATTENTE'
        END
    """)
    nb = c.execute("SELECT changes()").fetchone()[0]
    print(f"[OK] statut ajoute et synchronise dans candidatures ({nb} lignes mises a jour)")
else:
    print("[INFO] statut deja present dans candidatures")

conn.commit()
conn.close()

print("\n[SUCCESS] Migration terminee avec succes !")
