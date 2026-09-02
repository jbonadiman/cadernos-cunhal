from extract.text_filters import is_navigation_label

def test_digit_and_whitespace_only_is_a_navigation_label():
    assert is_navigation_label("1    2    3    4    5") is True

def test_single_digit_is_a_navigation_label():
    assert is_navigation_label("1") is True

def test_prose_text_is_not_a_navigation_label():
    text = "Álvaro Barreirinhas Cunhal, natural de Coimbra, de 43 anos de idade"
    assert is_navigation_label(text) is False

def test_prose_containing_digits_is_not_a_navigation_label():
    assert is_navigation_label("acórdão de 9 de Maio de 1950 do Tribunal") is False

def test_empty_or_whitespace_only_is_not_treated_as_navigation():
    assert is_navigation_label("   ") is False
    assert is_navigation_label("") is False
