from extract.extract_images import output_filename

def test_output_filename_zero_pads_to_total_width():
    assert output_filename(1, 28) == "01.jpg"
    assert output_filename(28, 28) == "28.jpg"

def test_output_filename_adapts_width_to_total():
    assert output_filename(1, 5) == "1.jpg"
    assert output_filename(1, 100) == "001.jpg"
