"""
Parcours académiques UniSphere (style ESPRIT).

Informatique : 1A/2A (TC) → 3A ou 3IA → 4A/5A (Fintech, DAS-info, SSA, Actuariat)
Électromécanique : 1EM/2EM/3EM → 4A/5A (OGI, MecaT, option Air)
Génie Civil : 1GC → 5GC
"""


class Filiere:
    INFO = "info"
    EM = "em"
    GC = "gc"
    LABELS = {
        INFO: "Informatique",
        EM: "Électromécanique",
        GC: "Génie Civil",
    }
    CHOICES = [(k, v) for k, v in LABELS.items()]


# (code, label, filiere, year)
PROGRAM_DEFS = [
    # Informatique — tronc commun
    ("1A", "1A — Tronc commun Info", Filiere.INFO, 1),
    ("2A", "2A — Tronc commun Info", Filiere.INFO, 2),
    # Informatique — 3ème
    ("3A", "3A — Info (continuité tronc commun)", Filiere.INFO, 3),
    ("3IA", "3IA — Intelligence Artificielle", Filiere.INFO, 3),
    # Informatique — 4ème / 5ème spécialités
    ("4A-FINTECH", "4A — Fintech", Filiere.INFO, 4),
    ("4A-DAS", "4A — DAS-info", Filiere.INFO, 4),
    ("4A-SSA", "4A — SSA", Filiere.INFO, 4),
    ("4A-ACTUARIAT", "4A — Actuariat", Filiere.INFO, 4),
    ("5A-FINTECH", "5A — Fintech", Filiere.INFO, 5),
    ("5A-DAS", "5A — DAS-info", Filiere.INFO, 5),
    ("5A-SSA", "5A — SSA", Filiere.INFO, 5),
    ("5A-ACTUARIAT", "5A — Actuariat", Filiere.INFO, 5),
    # Électromécanique
    ("1EM", "1EM — Électromécanique", Filiere.EM, 1),
    ("2EM", "2EM — Électromécanique", Filiere.EM, 2),
    ("3EM", "3EM — Électromécanique", Filiere.EM, 3),
    ("4EM-OGI", "4A EM — OGI", Filiere.EM, 4),
    ("4EM-MECAT", "4A EM — MecaT", Filiere.EM, 4),
    ("4EM-AIR", "4A EM — Option Air", Filiere.EM, 4),
    ("5EM-OGI", "5A EM — OGI", Filiere.EM, 5),
    ("5EM-MECAT", "5A EM — MecaT", Filiere.EM, 5),
    ("5EM-AIR", "5A EM — Option Air", Filiere.EM, 5),
    # Génie Civil
    ("1GC", "1GC — Génie Civil", Filiere.GC, 1),
    ("2GC", "2GC — Génie Civil", Filiere.GC, 2),
    ("3GC", "3GC — Génie Civil", Filiere.GC, 3),
    ("4GC", "4GC — Génie Civil", Filiere.GC, 4),
    ("5GC", "5GC — Génie Civil", Filiere.GC, 5),
]

PROGRAM_CHOICES = [(code, label) for code, label, _, _ in PROGRAM_DEFS]
PROGRAM_LABELS = {code: label for code, label, _, _ in PROGRAM_DEFS}
PROGRAM_FILIERE = {code: fil for code, _, fil, _ in PROGRAM_DEFS}
PROGRAM_YEAR = {code: year for code, _, _, year in PROGRAM_DEFS}

# Grouped for <optgroup> in forms
PROGRAM_GROUPS = [
    (
        "Informatique — Tronc commun",
        [("1A", "1A — Tronc commun"), ("2A", "2A — Tronc commun")],
    ),
    (
        "Informatique — 3ème année",
        [("3A", "3A — Continuité TC"), ("3IA", "3IA — Intelligence Artificielle")],
    ),
    (
        "Informatique — 4ème année (spécialité)",
        [
            ("4A-FINTECH", "4A — Fintech"),
            ("4A-DAS", "4A — DAS-info"),
            ("4A-SSA", "4A — SSA"),
            ("4A-ACTUARIAT", "4A — Actuariat"),
        ],
    ),
    (
        "Informatique — 5ème année (spécialité)",
        [
            ("5A-FINTECH", "5A — Fintech"),
            ("5A-DAS", "5A — DAS-info"),
            ("5A-SSA", "5A — SSA"),
            ("5A-ACTUARIAT", "5A — Actuariat"),
        ],
    ),
    (
        "Électromécanique — 1EM à 3EM",
        [
            ("1EM", "1EM"),
            ("2EM", "2EM"),
            ("3EM", "3EM"),
        ],
    ),
    (
        "Électromécanique — 4ème année (spécialité)",
        [
            ("4EM-OGI", "4A — OGI"),
            ("4EM-MECAT", "4A — MecaT"),
            ("4EM-AIR", "4A — Option Air"),
        ],
    ),
    (
        "Électromécanique — 5ème année (spécialité)",
        [
            ("5EM-OGI", "5A — OGI"),
            ("5EM-MECAT", "5A — MecaT"),
            ("5EM-AIR", "5A — Option Air"),
        ],
    ),
    (
        "Génie Civil",
        [
            ("1GC", "1GC"),
            ("2GC", "2GC"),
            ("3GC", "3GC"),
            ("4GC", "4GC"),
            ("5GC", "5GC"),
        ],
    ),
]

# Map old demo values → new codes
LEGACY_LEVEL_MAP = {
    "beginner": "1A",
    "intermediate": "2A",
    "advanced": "3A",
}


def programs_for_filiere(filiere: str):
    return [
        (code, label)
        for code, label, fil, _ in PROGRAM_DEFS
        if fil == filiere
    ]


def filiere_label(code: str) -> str:
    return Filiere.LABELS.get(PROGRAM_FILIERE.get(code, ""), "—")


# Départements officiels (liste déroulante module)
# slug → niveaux destinés affichés
DEPARTMENT_DEFS = [
    {
        "slug": "tronc-commun",
        "name": "Département Tronc-Commun",
        "color": "#3b5bdb",
        "levels": ["1A", "2A"],
    },
    {
        "slug": "informatique",
        "name": "Département Informatique",
        "color": "#845ef7",
        "levels": [
            "3A",
            "3IA",
            "4A-FINTECH",
            "4A-DAS",
            "4A-SSA",
            "4A-ACTUARIAT",
            "5A-FINTECH",
            "5A-DAS",
            "5A-SSA",
            "5A-ACTUARIAT",
        ],
    },
    {
        "slug": "em",
        "name": "Département EM",
        "color": "#e8a317",
        "levels": [
            "1EM",
            "2EM",
            "3EM",
            "4EM-OGI",
            "4EM-MECAT",
            "4EM-AIR",
            "5EM-OGI",
            "5EM-MECAT",
            "5EM-AIR",
        ],
    },
    {
        "slug": "gc",
        "name": "Département GC",
        "color": "#e07a5f",
        "levels": ["1GC", "2GC", "3GC", "4GC", "5GC"],
    },
]

DEPARTMENT_SLUGS = [d["slug"] for d in DEPARTMENT_DEFS]
DEPARTMENT_LEVELS = {d["slug"]: d["levels"] for d in DEPARTMENT_DEFS}
LEVEL_TO_DEPARTMENT = {
    code: d["slug"] for d in DEPARTMENT_DEFS for code in d["levels"]
}


def programs_for_department(slug: str):
    """Niveaux destinés pour un département (slug)."""
    codes = DEPARTMENT_LEVELS.get(slug or "", [])
    return [(c, PROGRAM_LABELS[c]) for c in codes if c in PROGRAM_LABELS]


def department_slug_for_level(level: str) -> str:
    return LEVEL_TO_DEPARTMENT.get(level or "", "")


def ensure_departments():
    """Crée / met à jour les 4 départements officiels."""
    from .models import Category

    cats = {}
    for d in DEPARTMENT_DEFS:
        cat, _ = Category.objects.get_or_create(
            slug=d["slug"],
            defaults={"name": d["name"], "color": d["color"]},
        )
        if cat.name != d["name"] or cat.color != d["color"]:
            cat.name = d["name"]
            cat.color = d["color"]
            cat.save(update_fields=["name", "color"])
        cats[d["slug"]] = cat
    return cats


def dept_levels_by_category_id():
    """
    Mapping {category_id: [[code, label], ...]} pour le JS du formulaire module.
    """
    from .models import Category

    ensure_departments()
    mapping = {}
    for cat in Category.objects.filter(slug__in=DEPARTMENT_SLUGS):
        mapping[str(cat.pk)] = programs_for_department(cat.slug)
    return mapping
