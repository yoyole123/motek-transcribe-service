from transcriber.utils import sanitize_filename


def test_sanitize_filename_reserved_chars():
    original = 'my:bad*name?<>|"file.mp3'
    sanitized = sanitize_filename(original)
    assert 'my' in sanitized
    assert 'bad' in sanitized
    assert 'name' in sanitized
    for ch in '<>:"/\\|?*':
        assert ch not in sanitized


def test_sanitize_filename_empty_after_cleanup():
    original = '::::****????'  # becomes empty then fallback
    sanitized = sanitize_filename(original)
    assert sanitized.startswith('file')


def test_sanitize_filename_length_limit():
    long_name = 'a' * 300
    sanitized = sanitize_filename(long_name)
    assert len(sanitized) == 200
