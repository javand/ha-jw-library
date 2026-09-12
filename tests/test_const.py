"""Test constants for jw_library."""

from custom_components.jw_library.const import (
    ATTRIBUTION,
    CONF_LANGUAGE,
    DEFAULT_LANGUAGE,
    DOMAIN,
    JW_MEDIA_API_URL,
    LANGUAGE_CODE_MAP,
    LANGUAGE_PREFIXES,
    NAME,
    SUPPORTED_LANGUAGES,
    VERSION,
    WOL_BASE_URL,
)


def test_constants() -> None:
    """Test basic constants."""
    assert DOMAIN == "jw_library"
    assert NAME == "JW Library"
    assert VERSION == "0.1.0"
    assert "Watchtower" in ATTRIBUTION
    assert CONF_LANGUAGE == "language"
    assert DEFAULT_LANGUAGE == "english"
    assert WOL_BASE_URL == "https://wol.jw.org"
    assert "GETPUBMEDIALINKS" in JW_MEDIA_API_URL


def test_language_mappings() -> None:
    """Test language prefix and code mappings."""
    assert LANGUAGE_PREFIXES["lp-e"] == "en"
    assert LANGUAGE_PREFIXES["lp-s"] == "es"
    assert LANGUAGE_PREFIXES["lp-f"] == "fr"

    assert LANGUAGE_CODE_MAP["english"] == "lp-e"
    assert LANGUAGE_CODE_MAP["spanish"] == "lp-s"
    assert LANGUAGE_CODE_MAP["lp-e"] == "lp-e"

    for lang in SUPPORTED_LANGUAGES:
        assert lang in LANGUAGE_CODE_MAP
