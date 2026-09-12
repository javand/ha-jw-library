"""Unit tests for JWLibraryApiClient and text parsers."""

from datetime import date
from http import HTTPStatus
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.jw_library.api import (
    BIBLE_BOOK_NAMES,
    DailyTextEntry,
    JWDailyTextData,
    JWLibraryApiClient,
    JWLibraryApiClientCommunicationError,
    clean_commentary_scriptures,
    clean_tts_scriptures,
    expand_bible_citation,
    parse_bible_citation,
    strip_html,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    """Load a fixture file as string."""
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_strip_html() -> None:
    """Test HTML tag stripping and entity decoding."""
    html = "<p>Hello &amp; welcome</p><div>New line</div>"
    assert strip_html(html) == "Hello & welcome New line"


def test_clean_tts_scriptures() -> None:
    """Test removal of citations for TTS readability."""
    raw = (
        "They knew that he promised to drive out enemies, (Ex. 34:11; Josh. 9:24) "
        "so they sought peace. Like the apostle Paul wrote, 2 Ki. 5:14, we should "
        "have faith. In addition, (Read Deuteronomy 7:1) they obeyed God."
    )
    cleaned = clean_tts_scriptures(raw)
    assert "(Ex. 34:11; Josh. 9:24)" not in cleaned
    assert "(Read Deuteronomy 7:1)" not in cleaned
    assert "2 Ki. 5:14" not in cleaned
    assert (
        "so they sought peace. Like the apostle Paul wrote, we should have faith."
        in cleaned
    )


def test_clean_commentary_scriptures() -> None:
    """Test cleaning scripture citations from commentary text."""
    # Parenthetical citations
    raw = "We must show courage (Josh. 10:1; 2 Ki. 5:14) in all circumstances."
    cleaned = clean_commentary_scriptures(raw)
    assert "(Josh. 10:1; 2 Ki. 5:14)" not in cleaned
    assert cleaned == "We must show courage in all circumstances."

    # Comma-enclosed citations
    raw_comma = "Like David, 1 Sam. 17:45, we trust in Jehovah."
    assert clean_commentary_scriptures(raw_comma) == "Like David, we trust in Jehovah."

    # Parenthetical with Read prefix and dash range
    assert (
        clean_commentary_scriptures("Study faithfully (Read Josh. 1:8).")
        == "Study faithfully."
    )
    assert (
        clean_commentary_scriptures("Love never fails (1 Cor. 13:4-8).")
        == "Love never fails."
    )
    assert (
        clean_commentary_scriptures("Love never fails (1 Cor. 13:4\u20138).")
        == "Love never fails."
    )

    # Empty text
    assert clean_commentary_scriptures("") == ""


def test_expand_bible_citation() -> None:
    """Test expansion of abbreviated Bible citations."""
    assert expand_bible_citation("Matt. 6:33") == "Matthew 6:33"
    assert expand_bible_citation("2 Ki. 5:14") == "2 Kings 5:14"
    assert expand_bible_citation("Ps. 23:1") == "Psalms 23:1"
    assert expand_bible_citation("Song 1:1") == "Song of Solomon 1:1"
    assert expand_bible_citation("Song of Solomon 1:1") == "Song of Solomon 1:1"
    assert expand_bible_citation("1 Cor. 13:4-8") == "1 Corinthians 13:4-8"
    assert expand_bible_citation("Genesis 1:1") == "Genesis 1:1"
    assert expand_bible_citation("1   Sam. 17:45") == "1 Samuel 17:45"
    assert expand_bible_citation("") == ""
    assert expand_bible_citation("   ") == ""


def test_bible_book_names_reexported() -> None:
    """Test BIBLE_BOOK_NAMES is re-exported from api module for backward compatibility."""
    assert isinstance(BIBLE_BOOK_NAMES, dict)
    assert BIBLE_BOOK_NAMES.get("gen") == "Genesis"


def test_parse_bible_citation() -> None:
    """Test parsing Bible reading citation header."""
    book_name, book_num, start_ch, end_ch = parse_bible_citation("JEREMIAH 32-33")
    assert book_name == "Jeremiah"
    assert book_num == 24
    assert start_ch == 32
    assert end_ch == 33

    book_name, book_num, start_ch, end_ch = parse_bible_citation("GENESIS 1")
    assert book_name == "Genesis"
    assert book_num == 1
    assert start_ch == 1
    assert end_ch == 1

    book_name, book_num, start_ch, end_ch = parse_bible_citation("1 CORINTHIANS 13")
    assert book_name == "1 Corinthians"
    assert book_num == 46
    assert start_ch == 13
    assert end_ch == 13


def test_parse_meetings_page() -> None:
    """Test meeting overview page parsing."""
    html = load_fixture("meetings.html")
    client = JWLibraryApiClient(session=MagicMock())
    result = client._parse_meetings_page(html)

    assert result["workbook_url"] == "/en/wol/d/r1/lp-e/202026252"
    assert result["watchtower_url"] == "/en/wol/d/r1/lp-e/2026482"
    assert "September 7-13" in result["week_date_range"]


def test_parse_watchtower_page() -> None:
    """Test parsing of Watchtower study article page."""
    html = load_fixture("watchtower.html")
    client = JWLibraryApiClient(session=MagicMock())
    article = client._parse_watchtower_page(html, doc_id="2026482")

    assert article.title == "Learn From the Gibeonites"
    assert article.date_range == "SEPTEMBER 7-13, 2026"
    assert "JOSH. 10:1" in article.theme_scripture
    assert len(article.songs) >= 1
    assert "88" in article.songs[0]
    assert article.issue == "202607"
    assert article.doc_id == "2026482"
    # Verify cleaned text contains article content and questions
    assert "Identify lessons we can learn" in article.text
    assert "(Josh. 9:3)" not in article.text


def test_parse_watchtower_page_context_ttl() -> None:
    """Test parsing of Watchtower study article page with contextTtl date range."""
    html = """
    <p class="contextTtl du-color--white" id="p1" data-pid="1">
      <span id="page2" class="pageNum"></span><strong>SEPTEMBER 7-13, 2026</strong>
    </p>
    <h1>Title</h1>
    """
    client = JWLibraryApiClient(session=MagicMock())
    article = client._parse_watchtower_page(html, doc_id="123")
    assert article.date_range == "SEPTEMBER 7-13, 2026"


def test_parse_workbook_page() -> None:
    """Test parsing of workbook page."""
    html = load_fixture("workbook.html")
    client = JWLibraryApiClient(session=MagicMock())
    citation, book_name, book_num, ch_start, ch_end = client._parse_workbook_page(
        html, doc_id="202026252"
    )

    assert citation == "JEREMIAH 32-33"
    assert book_name == "Jeremiah"
    assert book_num == 24
    assert ch_start == 32
    assert ch_end == 33


def test_parse_bible_chapter() -> None:
    """Test verse extraction from Bible chapter page."""
    html = load_fixture("bible_chapter.html")
    client = JWLibraryApiClient(session=MagicMock())
    text = client._parse_bible_chapter(html)

    assert "The word that came to Jeremiah" in text
    assert "armies of the king of Babylon were besieging Jerusalem" in text


@pytest.mark.asyncio
async def test_api_client_network_calls() -> None:
    """Test full data retrieval using mocked aiohttp session."""
    meetings_html = load_fixture("meetings.html")
    watchtower_html = load_fixture("watchtower.html")
    workbook_html = load_fixture("workbook.html")
    bible_chapter_html = load_fixture("bible_chapter.html")
    pub_media_w_json = load_fixture("pub_media_w.json")
    pub_media_nwt_json = load_fixture("pub_media_nwt.json")
    daily_text_html = """
    <div class="todayItems">
      <h2>Thursday, September 10</h2>
      <p class="themeScrp">Trust in Jehovah with all your heart.—Prov. 3:5.</p>
      <div class="bodyTxt">
        <p>We should always rely on Jehovah. w24.06 10 ¶7</p>
      </div>
    </div>
    """

    mock_session = MagicMock(spec=aiohttp.ClientSession)
    url_to_content = {
        "meetings": meetings_html,
        "2026482": watchtower_html,
        "202026252": workbook_html,
        "nwtsty/24": bible_chapter_html,
        "pub=w": pub_media_w_json,
        "pub=nwt": pub_media_nwt_json,
        "/dt/r1/": daily_text_html,
    }

    def mock_get(url: str, **kwargs):
        content = next((v for k, v in url_to_content.items() if k in url), "")
        resp = MagicMock(status=HTTPStatus.OK)
        resp.text = AsyncMock(return_value=content)
        cm = AsyncMock()
        cm.__aenter__.return_value = resp
        cm.__aexit__.return_value = None
        return cm

    mock_session.request = mock_get
    mock_session.get = mock_get

    client = JWLibraryApiClient(session=mock_session, language="english")
    data = await client.async_get_library_data(base_date=date(2026, 9, 10))

    assert data.this_week is not None
    assert data.next_week is not None

    # Verify Watchtower data
    assert data.this_week.watchtower.title == "Learn From the Gibeonites"
    assert (
        data.this_week.watchtower.audio_url
        == "https://cfp2.jw-cdn.org/a/ee2f00/1/o/w_E_202607_01.mp3"
    )

    # Verify Bible reading data
    assert data.this_week.bible_reading.citation == "JEREMIAH 32-33"
    assert (
        data.this_week.bible_reading.audio_url
        == "https://cfp2.jw-cdn.org/a/c19846/1/o/nwt_24_Jer_E_32.mp3"
    )
    assert len(data.this_week.bible_reading.audio_urls) == 2
    assert data.this_week.bible_reading.audio_urls[1]["chapter"] == 33

    # Verify Daily Text data
    assert data.daily_text is not None
    assert data.daily_text.today.date == "2026-09-10"
    assert data.daily_text.today.day_and_date == "Thursday, September 10"
    assert data.daily_text.today.scripture == "Proverbs 3:5"
    assert "Trust in Jehovah" in data.daily_text.today.scripture_text
    assert "We should always rely on Jehovah." in data.daily_text.today.comments
    assert data.daily_text.yesterday.date == "2026-09-09"
    assert data.daily_text.tomorrow.date == "2026-09-11"


@pytest.mark.asyncio
async def test_api_client_error_handling() -> None:
    """Test error handling when HTTP request fails."""
    mock_session = MagicMock(spec=aiohttp.ClientSession)

    resp = MagicMock()
    resp.status = HTTPStatus.INTERNAL_SERVER_ERROR
    cm = AsyncMock()
    cm.__aenter__.return_value = resp
    cm.__aexit__.return_value = None
    mock_session.request.return_value = cm

    client = JWLibraryApiClient(session=mock_session)
    with pytest.raises(JWLibraryApiClientCommunicationError):
        await client._async_fetch_text("https://example.com/fail")


@pytest.mark.asyncio
async def test_parse_daily_text_page() -> None:
    """Test parsing of WOL Daily Text HTML page."""
    html = """
    <div class="todayItems">
      <h2>Friday, September 11</h2>
      <p class="themeScrp">Keep seeking first the Kingdom.—Matt. 6:33.</p>
      <div class="bodyTxt">
        <p>Jesus gave wonderful advice (Luke 12:31). We must prioritize spiritual matters. w24.06 10 ¶7</p>
      </div>
    </div>
    """
    client = JWLibraryApiClient(session=MagicMock())
    entry = client._parse_daily_text_html("2026-09-11", html)

    assert entry.date == "2026-09-11"
    assert entry.day_and_date == "Friday, September 11"
    assert "Keep seeking first the Kingdom." in entry.scripture_text
    assert entry.scripture == "Matthew 6:33"
    assert "Jesus gave wonderful advice" in entry.comments
    assert "w24.06" not in entry.comments


def test_parse_daily_text_separators_and_fallbacks() -> None:
    """Test various citation separators and missing element fallbacks."""
    client = JWLibraryApiClient(session=MagicMock())

    # Fallback to "Daily Text" when <h2> is missing or empty
    entry_no_h2 = client._parse_daily_text_html("2026-09-11", "<div></div>")
    assert entry_no_h2.day_and_date == "Daily Text"
    assert entry_no_h2.scripture_text == ""
    assert entry_no_h2.scripture == ""
    assert entry_no_h2.comments == ""

    entry_empty_h2 = client._parse_daily_text_html("2026-09-11", "<h2>   </h2>")
    assert entry_empty_h2.day_and_date == "Daily Text"

    # En-dash separator (\u2013)
    entry_endash = client._parse_daily_text_html(
        "2026-09-11",
        '<p class="themeScrp">Trust in Jehovah.\u2013Prov. 3:5.</p>',
    )
    assert entry_endash.scripture_text == "Trust in Jehovah."
    assert entry_endash.scripture == "Proverbs 3:5"

    # Double hyphen separator (--)
    entry_dash2 = client._parse_daily_text_html(
        "2026-09-11",
        '<p class="themeScrp">Love never fails.--1 Cor. 13:4.</p>',
    )
    assert entry_dash2.scripture_text == "Love never fails."
    assert entry_dash2.scripture == "1 Corinthians 13:4"

    # Spaced hyphen separator ( - )
    entry_spaced = client._parse_daily_text_html(
        "2026-09-11",
        '<p class="themeScrp">The Lord is my shepherd. - Ps. 23:1.</p>',
    )
    assert entry_spaced.scripture_text == "The Lord is my shepherd."
    assert entry_spaced.scripture == "Psalms 23:1"

    # Dot hyphen separator (.-)
    entry_dot_dash = client._parse_daily_text_html(
        "2026-09-11",
        '<p class="themeScrp">Be courageous.-Josh. 1:9.</p>',
    )
    assert entry_dot_dash.scripture_text == "Be courageous"
    assert entry_dot_dash.scripture == "Joshua 1:9"

    # Single hyphen separator (-)
    entry_hyphen = client._parse_daily_text_html(
        "2026-09-11",
        '<p class="themeScrp">In the beginning-Gen. 1:1.</p>',
    )
    assert entry_hyphen.scripture_text == "In the beginning"
    assert entry_hyphen.scripture == "Genesis 1:1"

    # No separator at all
    entry_no_sep = client._parse_daily_text_html(
        "2026-09-11",
        '<p class="themeScrp">Just scripture without citation</p>',
    )
    assert entry_no_sep.scripture_text == "Just scripture without citation"
    assert entry_no_sep.scripture == ""

    # Comments without Watchtower reference
    entry_plain_comment = client._parse_daily_text_html(
        "2026-09-11",
        '<div class="bodyTxt"><p>Simple comment without issue ref.</p></div>',
    )
    assert entry_plain_comment.comments == "Simple comment without issue ref."


@pytest.mark.asyncio
async def test_async_get_daily_text_entry() -> None:
    """Test fetching and parsing single daily text entry with proper URL."""
    html = """
    <div class="todayItems">
      <h2>Friday, September 11</h2>
      <p class="themeScrp">Keep seeking first the Kingdom.—Matt. 6:33.</p>
      <div class="bodyTxt">
        <p>Jesus gave wonderful advice (Luke 12:31). We must prioritize spiritual matters. w24.06 10 ¶7</p>
      </div>
    </div>
    """
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    requested_urls: list[str] = []

    def mock_get(url: str, **kwargs):
        requested_urls.append(url)
        resp = MagicMock()
        resp.status = HTTPStatus.OK
        resp.text = AsyncMock(return_value=html)
        cm = AsyncMock()
        cm.__aenter__.return_value = resp
        cm.__aexit__.return_value = None
        return cm

    mock_session.request = mock_get
    mock_session.get = mock_get

    client = JWLibraryApiClient(session=mock_session, language="english")
    entry = await client.async_get_daily_text_entry(date(2026, 9, 11))

    assert isinstance(entry, DailyTextEntry)
    assert entry.date == "2026-09-11"
    assert entry.day_and_date == "Friday, September 11"
    assert entry.scripture == "Matthew 6:33"
    assert "Jesus gave wonderful advice" in entry.comments
    assert requested_urls == ["https://wol.jw.org/en/wol/dt/r1/lp-e/2026/09/11"]


@pytest.mark.asyncio
async def test_async_get_daily_text_data() -> None:
    """Test concurrent retrieval of yesterday, today, and tomorrow daily text."""
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    requested_urls: list[str] = []

    def mock_get(url: str, **kwargs):
        requested_urls.append(url)
        resp = MagicMock()
        resp.status = HTTPStatus.OK
        resp.text = AsyncMock(
            return_value="""
            <div class="todayItems">
              <h2>Sample Header</h2>
              <p class="themeScrp">Faith without works is dead.—Jas. 2:26.</p>
              <div class="bodyTxt">
                <p>Action is required. w24.06 10 ¶7</p>
              </div>
            </div>
            """
        )
        cm = AsyncMock()
        cm.__aenter__.return_value = resp
        cm.__aexit__.return_value = None
        return cm

    mock_session.request = mock_get
    mock_session.get = mock_get

    client = JWLibraryApiClient(session=mock_session, language="english")
    data = await client.async_get_daily_text_data(date(2026, 9, 10))

    assert isinstance(data, JWDailyTextData)
    assert data.yesterday.date == "2026-09-09"
    assert data.today.date == "2026-09-10"
    assert data.tomorrow.date == "2026-09-11"
    assert data.today.scripture == "James 2:26"
    assert len(requested_urls) == 3
    assert any("2026/09/09" in u for u in requested_urls)
    assert any("2026/09/10" in u for u in requested_urls)
    assert any("2026/09/11" in u for u in requested_urls)
