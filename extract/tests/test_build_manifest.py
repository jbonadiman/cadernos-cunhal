from extract.build_manifest import build_manifest_data


def test_produces_one_entry_per_page_with_sequential_numbering():
    pages = [
        {"source": "237", "type": "transcription"},
        {"source": "branco", "type": "blank"},
        {"source": "238", "type": "transcription"},
    ]
    data = build_manifest_data(pages, "Documentos de Peniche")
    assert data["title"] == "Documentos de Peniche"
    assert data["page_count"] == 3
    assert data["pages"] == [
        {"number": 1, "image": "pages/1.jpg", "type": "transcription"},
        {"number": 2, "image": "pages/2.jpg", "type": "blank"},
        {"number": 3, "image": "pages/3.jpg", "type": "transcription"},
    ]


def test_image_filenames_are_zero_padded_to_total_width():
    pages = [{"source": str(i), "type": "plain"} for i in range(1, 11)]
    data = build_manifest_data(pages, "Some Book")
    assert data["pages"][0]["image"] == "pages/01.jpg"
    assert data["pages"][9]["image"] == "pages/10.jpg"
