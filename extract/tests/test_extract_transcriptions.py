from extract.extract_transcriptions import assemble_page_transcription

def test_builds_ordered_prose_across_frames_and_drops_navigation_labels():
    frame_to_chars = {
        1: {2, 4},
        2: {9, 10, 12},
        3: {32, 33},
    }
    text_by_char_id = {
        9: "Álvaro Barreirinhas Cunhal, natural de Coimbra",
        10: "1    2    3    4",       # page-number footer, must be dropped
        12: "licenciado em Direito, preso político na Cadeia do Forte de Peniche",
        32: "elementos para ajuizar tanto da pessoa como dos factos",
        33: "válida, para o estudo de alguém",
    }

    result = assemble_page_transcription(frame_to_chars, text_by_char_id)

    assert result == (
        "Álvaro Barreirinhas Cunhal, natural de Coimbra\n"
        "licenciado em Direito, preso político na Cadeia do Forte de Peniche\n"
        "elementos para ajuizar tanto da pessoa como dos factos\n"
        "válida, para o estudo de alguém"
    )

def test_frame_with_no_text_characters_contributes_nothing():
    frame_to_chars = {1: {2, 4}, 2: {9}}
    text_by_char_id = {9: "Um parágrafo qualquer de texto transcrito aqui."}

    result = assemble_page_transcription(frame_to_chars, text_by_char_id)

    assert result == "Um parágrafo qualquer de texto transcrito aqui."

def test_page_with_only_navigation_labels_returns_empty_string():
    frame_to_chars = {1: {10}}
    text_by_char_id = {10: "1 2 3"}

    result = assemble_page_transcription(frame_to_chars, text_by_char_id)

    assert result == ""
