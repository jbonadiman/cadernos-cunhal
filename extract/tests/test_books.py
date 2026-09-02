from extract.books import BOOKS


def test_registry_has_all_five_books():
    assert set(BOOKS.keys()) == {
        "peniche", "caderno1", "caderno28", "caderno43", "inventario",
    }


def test_every_entry_has_an_exe_path_and_a_title():
    for slug, entry in BOOKS.items():
        assert entry["exe"].suffix == ".exe"
        assert entry["title"]


def test_peniche_title_is_the_full_book_name():
    assert BOOKS["peniche"]["title"] == "Documentos de Peniche"
