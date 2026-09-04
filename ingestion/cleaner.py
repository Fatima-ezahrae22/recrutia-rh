"""
Module : cleaner.py
Rôle   : Nettoyage et normalisation du texte brut extrait d'un CV.
         Supprime le bruit, normalise les espaces, corrige les encodages.

Auteur : Agent IA RH — Couche Ingestion
"""

import re
import unicodedata
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# Patterns de bruit connus dans les CV
# ─────────────────────────────────────────

# Caractères parasites fréquents en sortie OCR ou PDF
PATTERNS_BRUIT = [
    r"[|•·▪▸►▶➤✓✔★☆©®™°]",    # symboles décoratifs
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",  # caractères de contrôle
    r"(?<!\w)-{2,}(?!\w)",      # séparateurs type "---" non-tirets composés
    r"_{3,}",                   # lignes ____________
    r"\.{4,}",                  # points de suspension excessifs ......
    r"\s*\|\s*",                # séparateurs pipe entre mots
]

# En-têtes/pieds de page typiques à supprimer
PATTERNS_ENTETES = [
    r"Page\s*\d+\s*(sur|of|/)\s*\d+",   # "Page 1 sur 2"
    r"CV\s*[-–—]\s*\d{4}",              # "CV - 2024"
    r"Curriculum\s*Vitae",              # mentions redondantes
    r"^\s*\d{1,3}\s*$",                 # numéros de page seuls
]


# ─────────────────────────────────────────
# Étapes de nettoyage
# ─────────────────────────────────────────

def _normaliser_unicode(texte: str) -> str:
    """
    Normalise les caractères Unicode en NFC.
    Convertit les variantes d'apostrophes, guillemets, tirets vers leur forme standard.
    """
    texte = unicodedata.normalize("NFC", texte)
    # Remplacer les variantes typographiques
    remplacements = {
        "\u2018": "'", "\u2019": "'",   # guillemets simples typographiques
        "\u201c": '"', "\u201d": '"',   # guillemets doubles typographiques
        "\u2013": "-", "\u2014": "-",   # tirets demi-cadratin et cadratin
        "\u00a0": " ",                  # espace insécable
        "\u2022": "",                   # bullet point
        "\ufb01": "fi", "\ufb02": "fl", # ligatures PDF courantes
        "\ufb00": "ff", "\ufb03": "ffi",
    }
    for original, remplacement in remplacements.items():
        texte = texte.replace(original, remplacement)
    return texte


def _supprimer_bruit(texte: str) -> str:
    """Supprime les patterns de bruit et caractères parasites."""
    for pattern in PATTERNS_BRUIT:
        texte = re.sub(pattern, " ", texte, flags=re.MULTILINE)
    for pattern in PATTERNS_ENTETES:
        texte = re.sub(pattern, "", texte, flags=re.MULTILINE | re.IGNORECASE)
    return texte


def _normaliser_espaces(texte: str) -> str:
    """
    Normalise tous les espaces :
    - Réduit les espaces multiples à un seul
    - Supprime les lignes vides répétées (max 2 sauts de ligne consécutifs)
    - Retire les espaces en début/fin de ligne
    """
    # Espaces horizontaux multiples → un seul
    texte = re.sub(r"[ \t]+", " ", texte)
    # Début/fin de chaque ligne
    texte = "\n".join(ligne.strip() for ligne in texte.splitlines())
    # Lignes vides consécutives → max 2
    texte = re.sub(r"\n{3,}", "\n\n", texte)
    return texte.strip()


def _corriger_mots_coupes(texte: str) -> str:
    """
    Corrige les mots coupés par les sauts de ligne (artefact PDF/OCR).
    Ex : "Déve-\nloppeur" → "Développeur"
    """
    return re.sub(r"-\n(\w)", r"\1", texte)


def _supprimer_lignes_parasites(texte: str) -> str:
    """Supprime les lignes trop courtes ou composées uniquement de ponctuation."""
    lignes_propres = []
    for ligne in texte.splitlines():
        # Conserver les lignes d'au moins 2 caractères alphanumériques
        if len(re.findall(r"\w", ligne)) >= 2:
            lignes_propres.append(ligne)
        # Conserver les lignes vides séparatrices
        elif ligne.strip() == "":
            lignes_propres.append(ligne)
    return "\n".join(lignes_propres)


# ─────────────────────────────────────────
# Fonction principale
# ─────────────────────────────────────────

def nettoyer_texte(texte_brut: str) -> str:
    """
    Nettoie et normalise le texte brut extrait d'un CV.

    Pipeline appliqué dans l'ordre :
      1. Normalisation Unicode (NFC, ligatures, guillemets)
      2. Correction des mots coupés (artefact PDF)
      3. Suppression des caractères parasites et patterns de bruit
      4. Suppression des en-têtes/pieds de page redondants
      5. Suppression des lignes parasites (trop courtes ou sans contenu)
      6. Normalisation des espaces et sauts de ligne

    Args:
        texte_brut (str): Texte tel que sorti de l'extracteur.

    Returns:
        str: Texte nettoyé, prêt pour le parseur.
    """
    if not texte_brut or not texte_brut.strip():
        logger.warning("[Cleaner] Texte vide reçu.")
        return ""

    etapes = [
        ("Normalisation Unicode",         _normaliser_unicode),
        ("Correction mots coupés",        _corriger_mots_coupes),
        ("Suppression bruit",             _supprimer_bruit),
        ("Suppression lignes parasites",  _supprimer_lignes_parasites),
        ("Normalisation espaces",         _normaliser_espaces),
    ]

    texte = texte_brut
    for nom_etape, fn in etapes:
        texte = fn(texte)
        logger.debug(f"[Cleaner] '{nom_etape}' appliquée — {len(texte)} chars restants")

    logger.info(f"[Cleaner] Nettoyage terminé : {len(texte_brut)} → {len(texte)} caractères")
    return texte
