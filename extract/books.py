"""Registry of the five standalone book projectors on the disc: each
book's projector executable and its display title. Does not hold page
manifests directly (see extract/manifests/__init__.py's PAGES_BY_SLUG,
populated once every book's manifest exists)."""

from pathlib import Path

DISC_ROOT = Path("/run/media/user/Cadernos")

BOOKS = {
    "peniche": {
        "exe": DISC_ROOT / "4.Peniche.exe",
        "title": "Documentos de Peniche",
    },
    "caderno1": {
        "exe": DISC_ROOT / "1.Caderno_1.exe",
        "title": "Caderno 1",
    },
    "caderno28": {
        "exe": DISC_ROOT / "2.Caderno_28.exe",
        "title": "Caderno 28",
    },
    "caderno43": {
        "exe": DISC_ROOT / "3.Caderno_43.exe",
        "title": "Caderno 43",
    },
    "inventario": {
        "exe": DISC_ROOT / "5.Inventario.exe",
        "title": "Inventário",
    },
}
