"""
Module : parser.py
Rôle   : Extraction d'informations structurées depuis le texte nettoyé d'un CV.
         Identifie : compétences, années d'expérience, niveau de formation.

Auteur : Agent IA RH — Couche Ingestion
"""

import json
import re
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# Chargement de la liste de référence
# ─────────────────────────────────────────

def _charger_competences_reference() -> List[str]:
    """Charge la liste de compétences depuis le fichier JSON de référence."""
    chemin = Path(__file__).resolve().parent.parent / "data" / "competences_ref.json"
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[Parser] Impossible de charger competences_ref.json : {e}")
        return []


COMPETENCES_REFERENCE = _charger_competences_reference()


# ─────────────────────────────────────────
# 1. Extraction des compétences
# ─────────────────────────────────────────

# Sections de CV où les compétences sont le plus souvent listées
MOTS_CLES_SECTIONS_COMP = [
    r"comp[eé]tences?",
    r"skills?",
    r"technologies?",
    r"outils?",
    r"langages?",
    r"environnements?",
    r"stack",
]

REGEX_SECTION_COMP = re.compile(
    r"(?:" + "|".join(MOTS_CLES_SECTIONS_COMP) + r")\s*[:\-–]?\s*(.+?)(?=\n\n|\Z)",
    re.IGNORECASE | re.DOTALL,
)


ALIAS_COMPETENCES = {
    # Frontend & Web
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "angular": "Angular",
    "angularjs": "Angular",
    "html": "HTML5",
    "html5": "HTML5",
    "css": "CSS3",
    "css3": "CSS3",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    # Backend & Python
    "py": "Python",
    "python3": "Python",
    "dj": "Django",
    "django": "Django",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node": "Node.js",
    "express": "Express.js",
    "expressjs": "Express.js",
    "php": "PHP",
    "laravel": "Laravel",
    # Bases de données & Cloud
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "my sql": "MySQL",
    "mysql": "MySQL",
    "aws": "Amazon Web Services",
    "amazon web services": "Amazon Web Services",
    "gcp": "Google Cloud",
    "google cloud": "Google Cloud",
    "azure": "Microsoft Azure",
    "docker": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    # Data & AI & Design
    "sklearn": "Scikit-Learn",
    "scikit-learn": "Scikit-Learn",
    "tf": "TensorFlow",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "nlp": "NLP",
    "ia": "Intelligence Artificielle",
    "ai": "Intelligence Artificielle",
    "powerbi": "Power BI",
    "power bi": "Power BI",
    "ui/ux": "UI/UX Design",
    "ux/ui": "UI/UX Design",
    "figma": "Figma",
}


def normaliser_competence(comp: str) -> str:
    """Normalise un nom de compétence vers sa forme canonique de référence."""
    comp_clean = comp.strip().lower()
    return ALIAS_COMPETENCES.get(comp_clean, comp.strip())


def extraire_competences(texte: str) -> List[str]:
    """
    Identifie les compétences dans le texte en comparant à la liste de référence
    et au dictionnaire d'alias.

    Stratégie :
      1. Recherche d'abord dans les sections "Compétences / Skills / Technologies"
         (matching contextuel prioritaire)
      2. Scan global du texte entier en fallback
      3. Prise en compte des alias et abréviations (ex: JS -> JavaScript, Postgres -> PostgreSQL)

    Args:
        texte (str): Texte nettoyé du CV.

    Returns:
        List[str]: Liste ordonnée et dédupliquée des compétences détectées.
    """
    competences_trouvees = set()

    def _scan_texte(zone: str):
        """Scanne une zone de texte pour y trouver les compétences de référence et alias."""
        zone_lower = zone.lower()
        for comp in COMPETENCES_REFERENCE:
            # Pattern : mot entier, insensible à la casse
            pattern = r"(?<![a-zA-Z0-9])" + re.escape(comp.lower()) + r"(?![a-zA-Z0-9])"
            if re.search(pattern, zone_lower):
                competences_trouvees.add(comp)

        for alias, comp_standard in ALIAS_COMPETENCES.items():
            pattern = r"(?<![a-zA-Z0-9])" + re.escape(alias.lower()) + r"(?![a-zA-Z0-9])"
            if re.search(pattern, zone_lower):
                competences_trouvees.add(comp_standard)

    # --- Étape 1 : zones de compétences prioritaires ---
    sections = REGEX_SECTION_COMP.findall(texte)
    if sections:
        for section in sections:
            _scan_texte(section)
        logger.info(f"[Parser] Compétences extraites depuis section dédiée : {len(competences_trouvees)} trouvées")

    # --- Étape 2 : scan global si peu de résultats ---
    if len(competences_trouvees) < 3:
        logger.info("[Parser] Scan global du texte pour les compétences")
        _scan_texte(texte)

    result = sorted(competences_trouvees)
    logger.info(f"[Parser] {len(result)} compétence(s) détectée(s) : {result}")
    return result


# ─────────────────────────────────────────
# 2. Extraction des années d'expérience
# ─────────────────────────────────────────

# Patterns pour repérer la durée d'expérience dans un CV
PATTERNS_EXPERIENCE = [
    # Explicite : "X ans d'expérience"
    r"(\d{1,2})\s*(?:an(?:s|née(?:s)?)?)\s+d['\']?expérience",
    r"(\d{1,2})\s*(?:year(?:s)?)\s+(?:of\s+)?experience",
    # Fourchette : "3 à 5 ans"
    r"(\d{1,2})\s*[àa-]\s*\d{1,2}\s*an(?:s)?",
    # Plus de X ans
    r"(?:plus\s+de|more\s+than|over|depuis)\s+(\d{1,2})\s*an(?:s)?",
]

# Patterns pour détecter des plages d'années (calcul automatique)
PATTERNS_DATES_EMPLOI = [
    # "2019 - 2023", "Janv. 2020 – Mars 2024", "01/2021 - 12/2023"
    r"(?:jan(?:vier)?|fév(?:rier)?|mar(?:s)?|avr(?:il)?|mai|juin|juil(?:let)?|"
    r"août|sep(?:t(?:embre)?)?|oct(?:obre)?|nov(?:embre)?|déc(?:embre)?|"
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)?"
    r"\.?\s*(\d{4})\s*[-–—à/]\s*"
    r"(?:aujourd['\']?hui|présent|maintenant|current|present|now|(\d{4}))",
    r"(\d{4})\s*[-–—]\s*(\d{4})",
]


def _extraire_depuis_plages(texte: str) -> Optional[int]:
    """
    Calcule le nombre d'années d'expérience en totalisant les plages de dates détectées.
    Retourne None si aucune plage fiable trouvée.
    """
    import datetime
    annee_courante = datetime.date.today().year
    total_mois = 0
    experiences = []

    for pattern in PATTERNS_DATES_EMPLOI:
        for match in re.finditer(pattern, texte, re.IGNORECASE):
            groupes = [g for g in match.groups() if g]
            annees = [int(g) for g in groupes if g and g.isdigit() and 1970 <= int(g) <= annee_courante + 1]
            if len(annees) == 2:
                debut, fin = annees[0], annees[1]
                if debut <= fin:
                    experiences.append((debut, fin))
            elif len(annees) == 1:
                # Correspond à "présent" ou "aujourd'hui"
                debut = annees[0]
                if debut <= annee_courante:
                    experiences.append((debut, annee_courante))

    if not experiences:
        return None

    # Fusion des périodes chevauchantes pour éviter le double comptage
    experiences.sort()
    periodes_fusionnees = [experiences[0]]
    for debut, fin in experiences[1:]:
        if debut <= periodes_fusionnees[-1][1]:
            periodes_fusionnees[-1] = (
                periodes_fusionnees[-1][0],
                max(periodes_fusionnees[-1][1], fin),
            )
        else:
            periodes_fusionnees.append((debut, fin))

    total_annees = sum(fin - debut for debut, fin in periodes_fusionnees)
    return max(0, total_annees)


def extraire_experience_annees(texte: str) -> int:
    """
    Estime le nombre d'années d'expérience professionnelle.

    Stratégie en cascade :
      1. Mention explicite ("5 ans d'expérience")
      2. Calcul depuis les plages de dates des postes occupés
      3. Valeur par défaut : 0 (non détecté)

    Args:
        texte (str): Texte nettoyé du CV.

    Returns:
        int: Nombre estimé d'années d'expérience.
    """
    # Étape 1 : mentions explicites
    for pattern in PATTERNS_EXPERIENCE:
        match = re.search(pattern, texte, re.IGNORECASE)
        if match:
            annees = int(match.group(1))
            logger.info(f"[Parser] Expérience explicite trouvée : {annees} an(s)")
            return annees

    # Étape 2 : calcul depuis les dates
    annees_calculees = _extraire_depuis_plages(texte)
    if annees_calculees is not None:
        logger.info(f"[Parser] Expérience calculée depuis dates : {annees_calculees} an(s)")
        return annees_calculees

    logger.warning("[Parser] Expérience non détectée → valeur par défaut : 0")
    return 0


# ─────────────────────────────────────────
# 3. Extraction du niveau de formation
# ─────────────────────────────────────────

# Hiérarchie des formations, du plus élevé au plus bas
FORMATIONS_PAR_NIVEAU = [
    # Doctorat
    ("Doctorat / PhD",  [r"ph\.?d", r"doctorat", r"doctorate", r"thèse\s+de\s+doctorat"]),
    # Master / Ingénieur
    ("Master / Ingénieur",  [
        r"master\s*[12]?", r"m\.?sc\.?", r"m\.?eng\.?",
        r"ing[eé]nieur", r"grande\s+[eé]cole",
        r"mast[eè]re", r"mba",
        r"dipl[oô]me\s+d['\']ing[eé]nieur",
        r"[eé]cole\s+d['\']ing[eé]nieurs?",
        r"mohammadia",   # EMI reconnue explicitement
    ]),
    # Licence / Bachelor
    ("Licence / Bachelor",  [
        r"licence", r"bachelor", r"b\.?sc\.?", r"l[123]", r"undergraduate"
    ]),
    # BTS / DUT / BTS
    ("BTS / DUT",  [
        r"bts\b", r"dut\b", r"b\.t\.s\.?", r"d\.u\.t\.?",
        r"brevet\s+de\s+technicien\s+supérieur",
        r"diplôme\s+universitaire\s+de\s+technologie",
    ]),
    # Baccalauréat
    ("Baccalauréat",  [
        r"baccalauréat", r"bac\b", r"bac\+\d", r"terminale"
    ]),
]


def extraire_formation(texte: str) -> str:
    """
    Identifie le niveau de formation le plus élevé mentionné dans le CV.

    Stratégie :
      Parcourt les niveaux de formation du plus élevé au plus bas,
      retourne le premier niveau trouvé dans le texte.

    Args:
        texte (str): Texte nettoyé du CV.

    Returns:
        str: Libellé du niveau de formation, ou "Non spécifié" si aucun détecté.
    """
    texte_lower = texte.lower()

    for niveau, patterns in FORMATIONS_PAR_NIVEAU:
        for pattern in patterns:
            if re.search(pattern, texte_lower):
                logger.info(f"[Parser] Formation détectée : {niveau}")
                return niveau

    logger.warning("[Parser] Formation non détectée → 'Non spécifié'")
    return "Non spécifié"
