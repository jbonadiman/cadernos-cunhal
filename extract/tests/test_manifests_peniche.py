from extract.manifests.peniche import PAGES


def test_total_page_count_is_28():
    assert len(PAGES) == 28


def test_first_and_last_pages():
    assert PAGES[0] == {"source": "237", "type": "transcription"}
    assert PAGES[-1] == {"source": "263", "type": "transcription"}


def test_exactly_one_blank_page():
    blanks = [p for p in PAGES if p["type"] == "blank"]
    assert blanks == [{"source": "branco", "type": "blank"}]


def test_no_plain_pages_in_this_book():
    # every non-blank Peniche page carries a transcription overlay
    assert all(p["type"] in ("transcription", "blank") for p in PAGES)
