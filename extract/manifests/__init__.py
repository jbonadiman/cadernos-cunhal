"""Per-book recovered page manifests, keyed by the same slugs used in
extract.books.BOOKS."""

from extract.manifests import caderno1, caderno28, caderno43, inventario, peniche

PAGES_BY_SLUG = {
    "peniche": peniche.PAGES,
    "caderno1": caderno1.PAGES,
    "caderno28": caderno28.PAGES,
    "caderno43": caderno43.PAGES,
    "inventario": inventario.PAGES,
}
