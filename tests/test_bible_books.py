"""Unit tests for Bible book name and abbreviation mappings."""

from custom_components.jw_library.bible_books import BIBLE_BOOK_NAMES


def test_bible_book_names_key_abbreviations() -> None:
    """Test key book abbreviations exist and map accurately."""
    assert BIBLE_BOOK_NAMES["gen"] == "Genesis"
    assert BIBLE_BOOK_NAMES["matt"] == "Matthew"
    assert BIBLE_BOOK_NAMES["rev"] == "Revelation"
    assert BIBLE_BOOK_NAMES["song of solomon"] == "Song of Solomon"
    assert BIBLE_BOOK_NAMES["song"] == "Song of Solomon"
    assert BIBLE_BOOK_NAMES["1 sam"] == "1 Samuel"
    assert BIBLE_BOOK_NAMES["ps"] == "Psalms"


def test_bible_book_names_structure() -> None:
    """Test BIBLE_BOOK_NAMES contains all books and proper types."""
    assert isinstance(BIBLE_BOOK_NAMES, dict)
    assert len(BIBLE_BOOK_NAMES) == 67
    unique_books = set(BIBLE_BOOK_NAMES.values())
    assert len(unique_books) == 66

    for key, value in BIBLE_BOOK_NAMES.items():
        assert isinstance(key, str)
        assert isinstance(value, str)
        assert key == key.lower()
        assert len(value) > 0
