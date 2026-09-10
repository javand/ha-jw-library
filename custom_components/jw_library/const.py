"""Constants for the JW Library integration."""

import logging
from datetime import timedelta

LOGGER: logging.Logger = logging.getLogger(__package__)

DOMAIN: str = "jw_library"
NAME: str = "JW Library"
VERSION: str = "0.1.0"
ATTRIBUTION: str = "Data provided by Watchtower Bible and Tract Society of Pennsylvania"

DEFAULT_SCAN_INTERVAL: timedelta = timedelta(hours=12)

CONF_LANGUAGE: str = "language"
DEFAULT_LANGUAGE: str = "english"

LANGUAGE_PREFIXES: dict[str, str] = {
    "lp-e": "en",
    "lp-s": "es",
    "lp-f": "fr",
    "lp-x": "de",
    "lp-po": "pt",
    "lp-i": "it",
    "lp-j": "ja",
    "lp-k": "ko",
    "lp-m": "ru",
}

LANGUAGE_CODE_MAP: dict[str, str] = {
    "english": "lp-e",
    "spanish": "lp-s",
    "french": "lp-f",
    "german": "lp-x",
    "portuguese": "lp-po",
    "italian": "lp-i",
    "japanese": "lp-j",
    "korean": "lp-k",
    "russian": "lp-m",
    "lp-e": "lp-e",
    "lp-s": "lp-s",
    "lp-f": "lp-f",
    "lp-x": "lp-x",
    "lp-po": "lp-po",
    "lp-i": "lp-i",
    "lp-j": "lp-j",
    "lp-k": "lp-k",
    "lp-m": "lp-m",
}

# Supported languages in config flow
SUPPORTED_LANGUAGES: list[str] = [
    "english",
    "spanish",
    "french",
    "german",
    "portuguese",
    "italian",
    "japanese",
    "korean",
    "russian",
]

# Base API URLs
WOL_BASE_URL: str = "https://wol.jw.org"
JW_MEDIA_API_URL: str = "https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS"
