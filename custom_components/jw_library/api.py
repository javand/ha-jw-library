"""API Client and content parsers for JW Library."""

from __future__ import annotations

import asyncio
import datetime
import json
import re
import socket
from dataclasses import dataclass
from html.parser import HTMLParser
from http import HTTPStatus
from typing import Any

import aiohttp

from .bible_books import BIBLE_BOOK_NAMES
from .const import (
    DEFAULT_LANGUAGE,
    JW_MEDIA_API_URL,
    LANGUAGE_CODE_MAP,
    LANGUAGE_PREFIXES,
    LOGGER,
    WOL_BASE_URL,
)

BIBLE_BOOKS: dict[str, int] = {
    "genesis": 1,
    "gen": 1,
    "ge": 1,
    "exodus": 2,
    "ex": 2,
    "leviticus": 3,
    "lev": 3,
    "le": 3,
    "numbers": 4,
    "num": 4,
    "nu": 4,
    "deuteronomy": 5,
    "deut": 5,
    "de": 5,
    "joshua": 6,
    "josh": 6,
    "jos": 6,
    "judges": 7,
    "judg": 7,
    "jg": 7,
    "ruth": 8,
    "ru": 8,
    "1 samuel": 9,
    "1 sam": 9,
    "1sa": 9,
    "2 samuel": 10,
    "2 sam": 10,
    "2sa": 10,
    "1 kings": 11,
    "1 ki": 11,
    "1ki": 11,
    "2 kings": 12,
    "2 ki": 12,
    "2ki": 12,
    "1 chronicles": 13,
    "1 chron": 13,
    "1ch": 13,
    "2 chronicles": 14,
    "2 chron": 14,
    "2ch": 14,
    "ezra": 15,
    "ezr": 15,
    "nehemiah": 16,
    "neh": 16,
    "ne": 16,
    "esther": 17,
    "esth": 17,
    "es": 17,
    "job": 18,
    "jb": 18,
    "psalms": 19,
    "psalm": 19,
    "ps": 19,
    "proverbs": 20,
    "prov": 20,
    "pr": 20,
    "ecclesiastes": 21,
    "eccl": 21,
    "ec": 21,
    "song of solomon": 22,
    "song": 22,
    "ca": 22,
    "isaiah": 23,
    "isa": 23,
    "is": 23,
    "jeremiah": 24,
    "jer": 24,
    "je": 24,
    "lamentations": 25,
    "lam": 25,
    "la": 25,
    "ezekiel": 26,
    "ezek": 26,
    "eze": 26,
    "daniel": 27,
    "dan": 27,
    "da": 27,
    "hosea": 28,
    "hos": 28,
    "ho": 28,
    "joel": 29,
    "joe": 29,
    "jl": 29,
    "amos": 30,
    "am": 30,
    "obadiah": 31,
    "obad": 31,
    "ob": 31,
    "jonah": 32,
    "jon": 32,
    "jnh": 32,
    "micah": 33,
    "mic": 33,
    "mi": 33,
    "nahum": 34,
    "nah": 34,
    "na": 34,
    "habakkuk": 35,
    "hab": 35,
    "zephaniah": 36,
    "zeph": 36,
    "zep": 36,
    "haggai": 37,
    "hag": 37,
    "hg": 37,
    "zechariah": 38,
    "zech": 38,
    "zec": 38,
    "malachi": 39,
    "mal": 39,
    "matthew": 40,
    "matt": 40,
    "mt": 40,
    "mark": 41,
    "mrk": 41,
    "mr": 41,
    "luke": 42,
    "luk": 42,
    "lu": 42,
    "john": 43,
    "jhn": 43,
    "joh": 43,
    "jn": 43,
    "acts": 44,
    "ac": 44,
    "romans": 45,
    "rom": 45,
    "ro": 45,
    "1 corinthians": 46,
    "1 cor": 46,
    "1co": 46,
    "2 corinthians": 47,
    "2 cor": 47,
    "2co": 47,
    "galatians": 48,
    "gal": 48,
    "ga": 48,
    "ephesians": 49,
    "eph": 49,
    "philippians": 50,
    "phil": 50,
    "php": 50,
    "colossians": 51,
    "col": 51,
    "1 thessalonians": 52,
    "1 thess": 52,
    "1th": 52,
    "2 thessalonians": 53,
    "2 thess": 53,
    "2th": 53,
    "1 timothy": 54,
    "1 tim": 54,
    "1ti": 54,
    "2 timothy": 55,
    "2 tim": 55,
    "2ti": 55,
    "titus": 56,
    "tit": 56,
    "ti": 56,
    "philemon": 57,
    "philem": 57,
    "phm": 57,
    "hebrews": 58,
    "heb": 58,
    "james": 59,
    "jas": 59,
    "jm": 59,
    "1 peter": 60,
    "1 pet": 60,
    "1pe": 60,
    "2 peter": 61,
    "2 pet": 61,
    "2pe": 61,
    "1 john": 62,
    "1 jn": 62,
    "1jo": 62,
    "2 john": 63,
    "2 jn": 63,
    "2jo": 63,
    "3 john": 64,
    "3 jn": 64,
    "3jo": 64,
    "jude": 65,
    "jud": 65,
    "revelation": 66,
    "rev": 66,
    "re": 66,
}

BOOK_NAMES_CANONICAL: dict[int, str] = {
    1: "Genesis",
    2: "Exodus",
    3: "Leviticus",
    4: "Numbers",
    5: "Deuteronomy",
    6: "Joshua",
    7: "Judges",
    8: "Ruth",
    9: "1 Samuel",
    10: "2 Samuel",
    11: "1 Kings",
    12: "2 Kings",
    13: "1 Chronicles",
    14: "2 Chronicles",
    15: "Ezra",
    16: "Nehemiah",
    17: "Esther",
    18: "Job",
    19: "Psalms",
    20: "Proverbs",
    21: "Ecclesiastes",
    22: "Song of Solomon",
    23: "Isaiah",
    24: "Jeremiah",
    25: "Lamentations",
    26: "Ezekiel",
    27: "Daniel",
    28: "Hosea",
    29: "Joel",
    30: "Amos",
    31: "Obadiah",
    32: "Jonah",
    33: "Micah",
    34: "Nahum",
    35: "Habakkuk",
    36: "Zephaniah",
    37: "Haggai",
    38: "Zechariah",
    39: "Malachi",
    40: "Matthew",
    41: "Mark",
    42: "Luke",
    43: "John",
    44: "Acts",
    45: "Romans",
    46: "1 Corinthians",
    47: "2 Corinthians",
    48: "Galatians",
    49: "Ephesians",
    50: "Philippians",
    51: "Colossians",
    52: "1 Thessalonians",
    53: "2 Thessalonians",
    54: "1 Timothy",
    55: "2 Timothy",
    56: "Titus",
    57: "Philemon",
    58: "Hebrews",
    59: "James",
    60: "1 Peter",
    61: "2 Peter",
    62: "1 John",
    63: "2 John",
    64: "3 John",
    65: "Jude",
    66: "Revelation",
}


class HTMLStripper(HTMLParser):
    """Simple HTML text stripper."""

    def __init__(self) -> None:
        """Initialize the HTML stripper."""
        super().__init__(convert_charrefs=True)
        self.reset()
        self.text: list[str] = []

    def handle_data(self, data: str) -> None:
        """Collect text data."""
        self.text.append(data)

    def handle_endtag(self, tag: str) -> None:
        """Append space on block end tags to prevent word merging."""
        if tag in ("p", "div", "br", "li", "h1", "h2", "h3", "h4", "article"):
            self.text.append(" ")

    def get_data(self) -> str:
        """Return gathered text."""
        return "".join(self.text)


def strip_html(html_str: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    stripper = HTMLStripper()
    stripper.feed(html_str)
    raw = stripper.get_data()
    cleaned = raw.replace("\u200b", "").replace("\xa0", " ")
    return re.sub(r"\s+", " ", cleaned).strip()


def clean_tts_scriptures(text: str) -> str:
    """Remove scripture citations so TTS narrates naturally."""
    book_names_regex = (
        r"(?:[1-3]\s+)?(?:Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|"
        r"Samuel|Kings|Chronicles|Ezra|Nehemiah|Esther|Job|Psalms?|Proverbs|Ecclesiastes|"
        r"Song\s+of\s+Solomon|Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|"
        r"Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|Matthew|"
        r"Mark|Luke|John|Acts|Romans|Corinthians|Galatians|Ephesians|Philippians|Colossians|"
        r"Thessalonians|Timothy|Titus|Philemon|Hebrews|James|Peter|Jude|Revelation|"
        r"Gen\.?|Ex\.?|Lev\.?|Num\.?|Deut\.?|Josh\.?|Judg\.?|Ru\.?|Sam\.?|Ki\.?|Chron\.?|"
        r"Ezr\.?|Neh\.?|Esth\.?|Ps\.?|Prov\.?|Eccl\.?|Song\.?|Isa\.?|Jer\.?|Lam\.?|Ezek\.?|"
        r"Dan\.?|Hos\.?|Am\.?|Mic\.?|Nah\.?|Hab\.?|Zeph\.?|Hag\.?|Zech\.?|Mal\.?|Matt\.?|"
        r"Rom\.?|Cor\.?|Gal\.?|Eph\.?|Phil\.?|Col\.?|Thess\.?|Tim\.?|Tit\.?|Philem\.?|"
        r"Heb\.?|Jas\.?|Pet\.?|Rev\.?)"
    )

    sub_cite = (
        r"(?:" + book_names_regex + r"\s+\d+(?::\d+(?:[\u2013\-]\d+)?)?"
        r"|\d+(?::\d+(?:[\u2013\-]\d+)?)?)"
    )
    citation_regex = sub_cite + r"(?:,\s*\d+)*(?:\s*;\s*" + sub_cite + r"(?:,\s*\d+)*)*"

    # 1. Parenthetical citations like (Josh. 10:1) or (Read Deuteronomy 7:1)
    paren_regex = r"\s*\(\s*(?:[Rr]ead\s+)?(?:" + citation_regex + r")\.?\s*\)"
    text = re.sub(paren_regex, "", text)

    # 2. Comma-enclosed citations: ', 2 Ki. 5:14,' -> ','
    comma_regex = r",\s*(?:" + citation_regex + r")\s*,"
    text = re.sub(comma_regex, ",", text)

    # 3. Trailing citation after word/quote before punctuation
    text = re.sub(
        r"([\"'\w]),\s*(?:" + citation_regex + r")\s*(,|\.|\s)",
        r"\1\2",
        text,
    )

    # Clean double commas and whitespace
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def expand_bible_citation(citation: str) -> str:
    """Expand abbreviated book citation like 'Matt. 6:33' to 'Matthew 6:33'."""
    cleaned = citation.strip()
    match = re.match(
        r"^([1-3]?\s*(?:song\s+of\s+solomon|[A-Za-z]+))\.?\s*(.*)$",
        cleaned,
        re.IGNORECASE,
    )
    if not match:
        return cleaned
    book_part = match.group(1).strip().lower().rstrip(".")
    book_part = re.sub(r"\s+", " ", book_part)
    remainder = match.group(2).strip()
    expanded = BIBLE_BOOK_NAMES.get(book_part, book_part.title())
    return f"{expanded} {remainder}".strip()


_COMMENTARY_BOOKS = sorted(
    list(BIBLE_BOOK_NAMES.keys()) + list(set(BIBLE_BOOK_NAMES.values())),
    key=len,
    reverse=True,
)
_COMMENTARY_BOOKS_PATTERN = "|".join(
    re.escape(b).replace(r"\ ", r"\s+") for b in _COMMENTARY_BOOKS
)
_DASH_RANGE = r"[\u2013-]"
_COMMENTARY_SUB_CITE = (
    rf"(?:(?:{_COMMENTARY_BOOKS_PATTERN})\.?\s+)?\d+:\d+(?:{_DASH_RANGE}\d+)?"
)
_COMMENTARY_CITATION_REGEX = (
    rf"(?:{_COMMENTARY_BOOKS_PATTERN})\.?\s+\d+:\d+(?:{_DASH_RANGE}\d+)?"
    rf"(?:,\s*\d+)*(?:\s*;\s*{_COMMENTARY_SUB_CITE}(?:,\s*\d+)*)*"
)

_COMMENTARY_PAREN_REGEX = re.compile(
    rf"\s*\(\s*(?:[Rr]ead\s+)?(?:{_COMMENTARY_CITATION_REGEX})\.?\s*\)",
    flags=re.IGNORECASE,
)
_COMMENTARY_COMMA_REGEX = re.compile(
    rf",\s*(?:{_COMMENTARY_CITATION_REGEX})\s*,",
    flags=re.IGNORECASE,
)
_COMMENTARY_WORD_COMMA_REGEX = re.compile(
    rf"([\"'\w]),\s*(?:{_COMMENTARY_CITATION_REGEX})\s*(,|\.|\s)",
    flags=re.IGNORECASE,
)
_DOUBLE_COMMA_REGEX = re.compile(r",\s*,")
_WHITESPACE_REGEX = re.compile(r"\s+")


def clean_commentary_scriptures(text: str) -> str:
    """Remove inline scripture citations from commentary text for fluent TTS reading."""
    if not text:
        return text

    text = _COMMENTARY_PAREN_REGEX.sub("", text)
    text = _COMMENTARY_COMMA_REGEX.sub(",", text)
    text = _COMMENTARY_WORD_COMMA_REGEX.sub(r"\1\2", text)
    text = _DOUBLE_COMMA_REGEX.sub(",", text)
    text = _WHITESPACE_REGEX.sub(" ", text)
    return text.strip()


def parse_bible_citation(citation: str) -> tuple[str, int, int, int]:
    """
    Parse Bible citation like 'JEREMIAH 32-33' or 'GENESIS 1'.

    Returns (book_name, book_number, chapter_start, chapter_end).
    """
    cleaned = citation.strip()
    match = re.search(r"^(.*?)\s+(\d+)(?:\s*[\-\u2013]\s*(\d+))?$", cleaned)
    if not match:
        return cleaned.title(), 1, 1, 1

    raw_book = match.group(1).strip()
    ch_start = int(match.group(2))
    ch_end = int(match.group(3)) if match.group(3) else ch_start

    book_key = raw_book.lower().replace(".", "")
    book_num = BIBLE_BOOKS.get(book_key, 1)
    canonical_name = BOOK_NAMES_CANONICAL.get(book_num, raw_book.title())

    return canonical_name, book_num, ch_start, ch_end


def _extract_watchtower_date_range(html: str) -> str:
    """Extract study article date range from HTML."""
    for p_match in re.finditer(
        r'<p[^>]*class="[^"]*(?:pubRefs|contextTtl)[^"]*"[^>]*>(.*?)</p>',
        html,
        re.IGNORECASE | re.DOTALL,
    ):
        p_text = strip_html(p_match.group(1)).strip()
        range_match = re.search(
            r"^([A-Za-z]+\s+\d+(?:[-–]\d+)?(?:,\s*\d{4})?)\.?$",  # noqa: RUF001
            p_text,
            re.IGNORECASE,
        )
        if range_match:
            return range_match.group(1)
    return ""


@dataclass
class WatchtowerArticle:
    """Watchtower study article metadata and content."""

    title: str
    date_range: str
    theme_scripture: str
    songs: list[str]
    audio_url: str
    text: str
    issue: str
    doc_id: str


@dataclass
class BibleReadingEntry:
    """Weekly Bible reading metadata and content."""

    citation: str
    book_name: str
    book_number: int
    chapter_start: int
    chapter_end: int
    audio_url: str
    audio_urls: list[dict[str, Any]]
    text: str
    doc_id: str


@dataclass
class WeeklyStudyData:
    """Weekly study package containing Watchtower and Bible reading."""

    week_date_range: str
    year: int
    week_number: int
    watchtower: WatchtowerArticle
    bible_reading: BibleReadingEntry


@dataclass
class DailyTextEntry:
    """Data class for a single day's daily text."""

    date: str
    day_and_date: str
    scripture_text: str
    scripture: str
    comments: str


@dataclass
class JWDailyTextData:
    """Container for yesterday, today, and tomorrow daily text entries."""

    yesterday: DailyTextEntry
    today: DailyTextEntry
    tomorrow: DailyTextEntry


@dataclass
class JWLibraryData:
    """Consolidated study data for coordinator."""

    this_week: WeeklyStudyData
    next_week: WeeklyStudyData
    daily_text: JWDailyTextData | None = None


class JWLibraryApiClientError(Exception):
    """General API client error."""


class JWLibraryApiClientCommunicationError(JWLibraryApiClientError):
    """Communication error."""


class JWLibraryApiClientParseError(JWLibraryApiClientError):
    """HTML / data parsing error."""


def _raise_for_status(status: int, url: str) -> None:
    """Check HTTP status and raise if not OK."""
    if status != HTTPStatus.OK:
        msg = f"HTTP {status} from {url}"
        raise JWLibraryApiClientCommunicationError(msg)


class JWLibraryApiClient:
    """API client for WOL and JW media CDN."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        language: str = DEFAULT_LANGUAGE,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        clean_lang = language.lower() if isinstance(language, str) else DEFAULT_LANGUAGE
        self._language = LANGUAGE_CODE_MAP.get(clean_lang, DEFAULT_LANGUAGE)
        self._bible_audio_cache: dict[str, list[dict[str, Any]]] = {}

    @property
    def language(self) -> str:
        """Return configured language."""
        return self._language

    @property
    def lang_prefix(self) -> str:
        """Return URL prefix for language (e.g. 'en')."""
        return LANGUAGE_PREFIXES.get(self._language, "en")

    @property
    def pub_media_lang_code(self) -> str:
        """Return JW CDN language code (e.g. 'E', 'S', 'F')."""
        parts = self._language.split("-")
        return parts[1].upper() if len(parts) > 1 else "E"

    @property
    def cms_lang(self) -> str:
        """Return CMS language code (e.g. 'E', 'S', 'F')."""
        return self.pub_media_lang_code

    async def _async_fetch_text(self, url: str) -> str:
        """Fetch text from a URL with timeout and error handling."""
        try:
            async with asyncio.timeout(15):
                req = self._session.request(
                    method="GET",
                    url=url,
                    headers={"User-Agent": "Mozilla/5.0 (HomeAssistant)"},
                )
                if hasattr(req, "__aenter__"):
                    async with req as response:
                        _raise_for_status(response.status, url)
                        return await response.text()
                response = await req
                _raise_for_status(response.status, url)
                return await response.text()
        except TimeoutError as err:
            msg = f"Timeout fetching from {url}: {err}"
            raise JWLibraryApiClientCommunicationError(msg) from err
        except (aiohttp.ClientError, socket.gaierror) as err:
            msg = f"Error fetching from {url}: {err}"
            raise JWLibraryApiClientCommunicationError(msg) from err
        except JWLibraryApiClientError:
            raise
        except Exception as err:
            msg = f"Unexpected error fetching from {url}: {err}"
            raise JWLibraryApiClientError(msg) from err

    def _parse_meetings_page(self, html: str) -> dict[str, str]:
        """Extract workbook link, watchtower link, and week date range."""
        result: dict[str, str] = {
            "workbook_url": "",
            "watchtower_url": "",
            "week_date_range": "",
        }

        # Look for links to workbook and watchtower
        links = re.findall(
            r'<a[^>]+href="(/en/wol/d/r1/[^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL
        )
        for href, text in links:
            clean_text = strip_html(text)
            if "Workbook" in clean_text or "pub-mwb" in href:
                result["workbook_url"] = href
                # Week date range often prefixes the workbook title
                date_match = re.match(
                    r"^([A-Za-z]+\s+\d+(?:[\-\u2013]\d+)?)", clean_text
                )
                if date_match:
                    result["week_date_range"] = date_match.group(1).strip()
            elif "Watchtower" in clean_text or "pub-w" in href:
                result["watchtower_url"] = href

        # If not matched by text, inspect document IDs from pub links
        mwb_doc_len = 9
        wt_doc_len = 7
        if not result["workbook_url"] or not result["watchtower_url"]:
            all_doc_links = re.findall(r'/en/wol/d/r1/[^"/]+/(\d+)', html)
            for doc_id in all_doc_links:
                href = f"/en/wol/d/r1/{self._language}/{doc_id}"
                if len(doc_id) == mwb_doc_len and not result["workbook_url"]:
                    result["workbook_url"] = href
                elif len(doc_id) == wt_doc_len and not result["watchtower_url"]:
                    result["watchtower_url"] = href

        return result

    def _parse_watchtower_page(self, html: str, doc_id: str) -> WatchtowerArticle:
        """Parse Watchtower study article page."""
        # Title
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
        title = strip_html(h1_match.group(1)) if h1_match else "Watchtower Study"

        # Date range
        date_range = _extract_watchtower_date_range(html)

        # Theme scripture
        theme_match = re.search(
            r'<p[^>]*class="[^"]*themeScrp[^"]*"[^>]*>(.*?)</p>', html, re.DOTALL
        )
        theme_scripture = strip_html(theme_match.group(1)) if theme_match else ""

        # Songs
        songs: list[str] = []
        for p in re.findall(
            r'<p[^>]*class="[^"]*pubRefs[^"]*"[^>]*>(.*?)</p>', html, re.DOTALL
        ):
            clean_song = strip_html(p)
            if re.search(
                r"\b(?:SONG|CANCI[OÓ]N|CANTIQUE|LIED)\b", clean_song, re.IGNORECASE
            ):
                songs.append(clean_song)

        # Extract issue code (e.g. 202607 from 'w26 July')
        month_map = {
            "january": "01",
            "february": "02",
            "march": "03",
            "april": "04",
            "may": "05",
            "june": "06",
            "july": "07",
            "august": "08",
            "september": "09",
            "october": "10",
            "november": "11",
            "december": "12",
        }
        issue = ""
        # 1. Look for 'w26 July' pattern in documentDescription or text
        month_names_pattern = "|".join(month_map.keys())
        pattern = rf"\bw(\d{{2}})\s+({month_names_pattern})\b"
        desc_match = re.search(pattern, html, re.IGNORECASE)
        if desc_match:
            year_suffix = desc_match.group(1)
            raw_month = desc_match.group(2).lower()
            if raw_month in month_map:
                issue = f"20{year_suffix}{month_map[raw_month]}"

        # 2. Fallback to pub-wYY class
        if not issue:
            issue_match = re.search(r"pub-w(\d{2})", html)
            if issue_match:
                year_suffix = issue_match.group(1)
                issue_year = f"20{year_suffix}"
                found_month = "01"
                for m_name, m_num in month_map.items():
                    target = f"the-watchtower-{issue_year}/study-edition/{m_name}"
                    if target in html.lower():
                        found_month = m_num
                        break
                issue = f"{issue_year}{found_month}"
            else:
                issue = f"{datetime.datetime.now(datetime.UTC).year}01"

        # Article body paragraphs
        article_match = re.search(r"<article[^>]*>(.*?)</article>", html, re.DOTALL)
        body_html = article_match.group(1) if article_match else html
        paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", body_html, re.DOTALL)

        cleaned_paras: list[str] = []
        for p in paragraphs:
            clean_p = strip_html(p)
            if clean_p and not clean_p.startswith("SONG"):
                cleaned_paras.append(clean_tts_scriptures(clean_p))

        full_text = "\n\n".join(cleaned_paras)

        return WatchtowerArticle(
            title=title,
            date_range=date_range,
            theme_scripture=theme_scripture,
            songs=songs,
            audio_url="",
            text=full_text,
            issue=issue,
            doc_id=doc_id,
        )

    def _parse_workbook_page(
        self, html: str, doc_id: str = ""
    ) -> tuple[str, str, int, int, int]:
        """Extract Bible reading citation and chapter range."""
        _ = doc_id
        h2_match = re.search(
            r'<h2[^>]*><a[^>]+href="[^"]*(?:/bc/|nwtsty)[^"]*"[^>]*>(.*?)</a></h2>',
            html,
            re.DOTALL,
        )
        if not h2_match:
            h2_match = re.search(r"<h2[^>]*>(.*?)</h2>", html, re.DOTALL)

        raw_citation = strip_html(h2_match.group(1)) if h2_match else "Genesis 1"
        book_name, book_num, ch_start, ch_end = parse_bible_citation(raw_citation)
        return raw_citation, book_name, book_num, ch_start, ch_end

    def _parse_bible_chapter(self, html: str) -> str:
        """Extract verse text from Bible chapter HTML."""
        verses = re.findall(
            r'<span[^>]+class="[^"]*v[^"]*"[^>]*>(.*?)</span>',
            html,
            re.DOTALL,
        )
        cleaned_verses: list[str] = []
        for v in verses:
            # Strip footnote and cross-reference links
            v_clean = re.sub(
                r"<a[^>]+class=\"[^\"]*(?:vp|cl|footnote)[^\"]*\"[^>]*>.*?</a>",
                "",
                v,
            )
            v_clean = strip_html(v_clean)
            # Remove margin symbols like * and +
            v_clean = re.sub(r"[\*\+]", "", v_clean).strip()
            if v_clean:
                cleaned_verses.append(v_clean)
        return " ".join(cleaned_verses)

    def _parse_daily_text_html(self, date_str: str, html: str) -> DailyTextEntry:
        """Parse WOL HTML into DailyTextEntry."""
        h2_match = re.search(r"<h2[^>]*>(.*?)</h2>", html, re.DOTALL)
        day_and_date = strip_html(h2_match.group(1)) if h2_match else "Daily Text"
        if not day_and_date:
            day_and_date = "Daily Text"

        scripture_text = ""
        scripture_citation = ""
        theme_match = re.search(
            r'<p[^>]*class="[^"]*themeScrp[^"]*"[^>]*>(.*?)</p>', html, re.DOTALL
        )
        if theme_match:
            raw_theme = strip_html(theme_match.group(1))
            parts: list[str] = []
            for sep in ("—", "\u2013", "--", " - ", ".-"):
                if sep in raw_theme:
                    parts = raw_theme.rsplit(sep, 1)
                    break
            if not parts and "-" in raw_theme:
                parts = raw_theme.rsplit("-", 1)

            if parts:
                scripture_text = parts[0].strip()
                raw_citation = parts[1].strip().rstrip(".")
                scripture_citation = expand_bible_citation(raw_citation).rstrip(".")
            else:
                scripture_text = raw_theme
                scripture_citation = ""

        comments = ""
        body_match = re.search(
            r'<div[^>]*class="[^"]*bodyTxt[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL
        )
        if body_match:
            raw_body = strip_html(body_match.group(1))
            raw_comments = re.sub(
                r"\s*w\d{2}(?:\.\d{2})?.*$", "", raw_body, flags=re.DOTALL
            ).strip()
            comments = clean_commentary_scriptures(raw_comments)

        return DailyTextEntry(
            date=date_str,
            day_and_date=day_and_date,
            scripture_text=scripture_text,
            scripture=scripture_citation,
            comments=comments,
        )

    async def async_get_watchtower_audio(
        self, issue: str, article_title: str, date_range: str
    ) -> str:
        """Query JW CDN pub-media API for Watchtower study MP3 link."""
        url = (
            f"{JW_MEDIA_API_URL}?output=json&pub=w&issue={issue}"
            f"&fileformat=MP3&alllangs=0&langwritten={self.cms_lang}&txtCMSLang={self.cms_lang}"
        )
        try:
            data_text = await self._async_fetch_text(url)
            data = json.loads(data_text)
            files = data.get("files", {}).get(self.cms_lang, {}).get("MP3", [])
            if not files:
                return ""

            # Attempt 1: Match by article title in track title
            clean_title = re.sub(r"[^\w\s]", "", article_title).lower()
            for track in files:
                t_title = track.get("title", "").lower()
                clean_track_title = re.sub(r"[^\w\s]", "", t_title)
                if clean_title and (
                    clean_title in clean_track_title or clean_track_title in clean_title
                ):
                    return track.get("file", {}).get("url", "")

            # Attempt 2: Match by date in track title (e.g. September 7-13)
            if date_range:
                clean_date = date_range.lower()
                for track in files:
                    if any(
                        part in track.get("title", "").lower()
                        for part in clean_date.split()
                    ):
                        return track.get("file", {}).get("url", "")

            # Attempt 3: Return first track as fallback
            return files[0].get("file", {}).get("url", "")
        except Exception as err:  # noqa: BLE001
            LOGGER.warning("Could not resolve Watchtower MP3: %s", err)
            return ""

    async def async_get_bible_audio(
        self, book_number: int, chapter_start: int, chapter_end: int
    ) -> tuple[str, list[dict[str, Any]]]:
        """Query JW CDN pub-media API for Bible chapters MP3 links."""
        cache_key = self.cms_lang
        if cache_key not in self._bible_audio_cache:
            url = (
                f"{JW_MEDIA_API_URL}?output=json&pub=nwt&fileformat=MP3"
                f"&alllangs=0&langwritten={self.cms_lang}&txtCMSLang={self.cms_lang}"
            )
            try:
                data_text = await self._async_fetch_text(url)
                data = json.loads(data_text)
                self._bible_audio_cache[cache_key] = (
                    data.get("files", {}).get(self.cms_lang, {}).get("MP3", [])
                )
            except Exception as err:  # noqa: BLE001
                LOGGER.warning("Could not fetch NWT Bible MP3 catalog: %s", err)
                return "", []

        mp3_list = self._bible_audio_cache.get(cache_key, [])
        chapter_urls: list[dict[str, Any]] = []

        for item in mp3_list:
            if item.get("booknum") == book_number:
                track_num = item.get("track", 0)
                if chapter_start <= track_num <= chapter_end:
                    url = item.get("file", {}).get("url", "")
                    chapter_urls.append(
                        {
                            "chapter": track_num,
                            "title": item.get("title", f"Chapter {track_num}"),
                            "url": url,
                        }
                    )

        chapter_urls.sort(key=lambda x: x["chapter"])
        primary_url = chapter_urls[0]["url"] if chapter_urls else ""
        return primary_url, chapter_urls

    async def async_get_weekly_data(
        self, target_date: datetime.date
    ) -> WeeklyStudyData:
        """Fetch all study materials for a specific week."""
        year, week_num, _ = target_date.isocalendar()
        meetings_url = (
            f"{WOL_BASE_URL}/{self.lang_prefix}/wol/meetings/r1/"
            f"{self._language}/{year}/{week_num}"
        )

        meetings_html = await self._async_fetch_text(meetings_url)
        parsed_links = self._parse_meetings_page(meetings_html)

        # 1. Fetch Watchtower article
        wt_url = parsed_links.get("watchtower_url", "")
        if not wt_url.startswith("http"):
            wt_url = f"{WOL_BASE_URL}{wt_url}"

        doc_id_match = re.search(r"/(\d+)$", wt_url)
        wt_doc_id = doc_id_match.group(1) if doc_id_match else ""

        wt_html = await self._async_fetch_text(wt_url)
        watchtower = self._parse_watchtower_page(wt_html, doc_id=wt_doc_id)

        # Resolve Watchtower audio
        wt_audio_url = await self.async_get_watchtower_audio(
            issue=watchtower.issue,
            article_title=watchtower.title,
            date_range=watchtower.date_range,
        )
        watchtower.audio_url = wt_audio_url

        # 2. Fetch Meeting Workbook & Bible reading
        wb_url = parsed_links.get("workbook_url", "")
        if not wb_url.startswith("http"):
            wb_url = f"{WOL_BASE_URL}{wb_url}"

        wb_doc_match = re.search(r"/(\d+)$", wb_url)
        wb_doc_id = wb_doc_match.group(1) if wb_doc_match else ""

        wb_html = await self._async_fetch_text(wb_url)
        citation, book_name, book_num, ch_start, ch_end = self._parse_workbook_page(
            wb_html, doc_id=wb_doc_id
        )

        # Fetch Bible reading text for chapter(s)
        chapter_texts: list[str] = []
        for ch in range(ch_start, ch_end + 1):
            ch_url = (
                f"{WOL_BASE_URL}/{self.lang_prefix}/wol/b/r1/{self._language}"
                f"/nwtsty/{book_num}/{ch}"
            )
            try:
                ch_html = await self._async_fetch_text(ch_url)
                ch_text = self._parse_bible_chapter(ch_html)
                if ch_text:
                    chapter_texts.append(ch_text)
            except (JWLibraryApiClientError, TimeoutError, aiohttp.ClientError) as err:
                LOGGER.warning("Could not fetch Bible chapter %s text: %s", ch, err)

        combined_bible_text = "\n\n".join(chapter_texts)

        # Resolve Bible audio
        primary_audio, all_audio = await self.async_get_bible_audio(
            book_number=book_num,
            chapter_start=ch_start,
            chapter_end=ch_end,
        )

        bible_reading = BibleReadingEntry(
            citation=citation,
            book_name=book_name,
            book_number=book_num,
            chapter_start=ch_start,
            chapter_end=ch_end,
            audio_url=primary_audio,
            audio_urls=all_audio,
            text=combined_bible_text,
            doc_id=wb_doc_id,
        )

        return WeeklyStudyData(
            week_date_range=parsed_links.get("week_date_range", ""),
            year=year,
            week_number=week_num,
            watchtower=watchtower,
            bible_reading=bible_reading,
        )

    async def async_get_daily_text_entry(
        self, date_val: datetime.date
    ) -> DailyTextEntry:
        """Fetch and parse daily text for a given date."""
        url = (
            f"{WOL_BASE_URL}/{self.lang_prefix}/wol/dt/r1/{self._language}/"
            f"{date_val.year}/{date_val.month:02d}/{date_val.day:02d}"
        )
        html = await self._async_fetch_text(url)
        return self._parse_daily_text_html(date_val.strftime("%Y-%m-%d"), html)

    async def async_get_daily_text_data(
        self, today_date: datetime.date
    ) -> JWDailyTextData:
        """Fetch yesterday, today, and tomorrow daily text concurrently."""
        yesterday_date = today_date - datetime.timedelta(days=1)
        tomorrow_date = today_date + datetime.timedelta(days=1)

        yesterday, today, tomorrow = await asyncio.gather(
            self.async_get_daily_text_entry(yesterday_date),
            self.async_get_daily_text_entry(today_date),
            self.async_get_daily_text_entry(tomorrow_date),
        )

        return JWDailyTextData(
            yesterday=yesterday,
            today=today,
            tomorrow=tomorrow,
        )

    async def async_get_library_data(
        self, base_date: datetime.date | None = None
    ) -> JWLibraryData:
        """Fetch weekly study materials and daily text concurrently."""
        target_today = base_date or datetime.datetime.now(datetime.UTC).date()
        next_week_date = target_today + datetime.timedelta(days=7)

        this_week, next_week, daily_text = await asyncio.gather(
            self.async_get_weekly_data(target_today),
            self.async_get_weekly_data(next_week_date),
            self.async_get_daily_text_data(target_today),
        )

        return JWLibraryData(
            this_week=this_week,
            next_week=next_week,
            daily_text=daily_text,
        )
