# JW Library Home Assistant Integration Design Specification

- **Date**: 2026-09-10
- **Domain**: `jw_library`
- **Repository**: `javand/ha-jw-library`
- **Reference**: `javand/ha-jw-daily-text`

---

## 1. Overview & Objectives

`ha-jw-library` is a Home Assistant custom integration distributed via HACS that provides the weekly Watchtower study article and weekly Bible reading from `jw.org` / `wol.jw.org`. 

### Key Capabilities
1. **Weekly Content Retrieval**: Scrapes Watchtower study articles and midweek meeting Life and Ministry Workbook pages from Watchtower Online Library (WOL) for both the **Current Week** and **Next Week**.
2. **Audio Streaming & Links**: Queries the official JW CDN pub-media API (`GETPUBMEDIALINKS`) to retrieve direct MP3 streaming URLs for the Watchtower study article and all assigned Bible reading chapters. These URLs can be fed directly to Home Assistant's native `media_player.play_media` service for Google Audio (Nest / Cast) speakers.
3. **Full Text & TTS Optimization**: Exposes full article text and Bible chapter text in sensor attributes, with scripture citations in parentheses and commas cleaned out using regex so text-to-speech (TTS) engines read the material fluently.
4. **Distinct Visual Identity**: Includes custom high-resolution branding assets (`icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png`) to immediately differentiate this integration from `ha-jw-daily-text` within HACS and Home Assistant.

---

## 2. Architecture & Components

```
                +------------------------------+
                |  Home Assistant Core / Event |
                +------------------------------+
                               |
                               ▼
        +----------------------------------------------+
        |        JWLibraryDataUpdateCoordinator        |
        |        (12-hour polling & week rollover)     |
        +----------------------------------------------+
                               |
                               ▼
        +----------------------------------------------+
        |              JWLibraryApiClient              |
        +----------------------------------------------+
                |                              |
                ▼                              ▼
     [WOL Scraping Service]        [JW CDN Pub-Media API]
  - /wol/meetings/r1/{lang}/{Y}/{W} - GETPUBMEDIALINKS?pub=w&issue=...
  - /wol/d/r1/... (Watchtower)      - GETPUBMEDIALINKS?pub=nwt
  - /wol/d/r1/... (Workbook)
  - /wol/b/r1/... (Bible verses)
                               |
                               ▼
                 +---------------------------+
                 |       Sensors (x4)        |
                 +---------------------------+
                 | - Watchtower This Week    |
                 | - Watchtower Next Week    |
                 | - Bible Reading This Week |
                 | - Bible Reading Next Week |
                 +---------------------------+
```

### Component Structure
- `custom_components/jw_library/`:
  - `__init__.py`: Component lifecycle, coordinator setup, config entry unload.
  - `manifest.json`: Integration metadata, domain `jw_library`, version, requirements, codeowners.
  - `const.py`: Domain constants, language maps, default scan intervals, attribution, API URLs.
  - `data.py`: Typed config entry and runtime data definitions.
  - `api.py`: `JWLibraryApiClient`, HTML strippers, citation cleaners, and data models (`WatchtowerArticle`, `BibleReadingEntry`, `WeeklyStudyData`, `JWLibraryData`).
  - `coordinator.py`: `JWLibraryDataUpdateCoordinator` managing async updates, calculating current/next calendar weeks, and exception translation.
  - `entity.py`: Base coordinator entity with shared device info (`identifiers={(DOMAIN, entry_id)}`, name: "JW Library").
  - `sensor.py`: `JWLibrarySensor` platform exposing the 4 sensors with dynamic state and rich attributes.
  - `config_flow.py`: UI configuration flow for language selection (English, Spanish, French, German, Portuguese, etc.).
  - `strings.json` & `translations/en.json`: UI copy for config flow and options.

---

## 3. Data Models & Entities

### Data Structures (`api.py`)
```python
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
class BibleChapterAudio:
    """Audio metadata for a single Bible chapter."""

    chapter: int
    title: str
    url: str


@dataclass
class BibleReadingEntry:
    """Weekly Bible reading metadata and content."""

    citation: str
    book_name: str
    book_number: int
    chapter_start: int
    chapter_end: int
    audio_url: str  # First chapter URL for simple casting
    audio_urls: list[dict[str, Any]]  # All chapters with titles and URLs
    text: str
    doc_id: str


@dataclass
class WeeklyStudyData:
    """Weekly package containing Watchtower and Bible reading."""

    week_date_range: str
    year: int
    week_number: int
    watchtower: WatchtowerArticle
    bible_reading: BibleReadingEntry


@dataclass
class JWLibraryData:
    """Coordinator payload with this week and next week study material."""

    this_week: WeeklyStudyData
    next_week: WeeklyStudyData
```

### Exposed Sensor Entities
1. `sensor.jw_watchtower_this_week`:
   - State: `WatchtowerArticle.title` (truncated to 255 chars)
   - Icon: `mdi:book-open-page-variant`
   - Attributes: `title`, `date_range`, `theme_scripture`, `songs`, `audio_url`, `text`, `issue`, `doc_id`
2. `sensor.jw_watchtower_next_week`:
   - State: `WatchtowerArticle.title`
   - Icon: `mdi:book-open-page-variant-outline`
   - Attributes: Same schema as above
3. `sensor.jw_bible_reading_this_week`:
   - State: `BibleReadingEntry.citation` (e.g. `"Jeremiah 32-33"`)
   - Icon: `mdi:book-cross` or `mdi:book-open-variant`
   - Attributes: `citation`, `book_name`, `book_number`, `chapter_start`, `chapter_end`, `audio_url`, `audio_urls`, `text`, `doc_id`
4. `sensor.jw_bible_reading_next_week`:
   - State: `BibleReadingEntry.citation`
   - Icon: `mdi:book-open-variant`
   - Attributes: Same schema as above

---

## 4. TTS Scripture Cleaning
To ensure natural speech when read through Google Assistant / Nabu Casa TTS, Watchtower paragraphs undergo regex cleanup:
- Strip parenthetical citations: `\s*\(\s*(?:[Rr]ead\s+)?(?:<citation_regex>)\.?\s*\)`
- Strip comma-enclosed citations: `,\s*(?:<citation_regex>)\s*,` -> `,`
- Strip trailing citations following quotation marks: `([\"'\w]),\s*(?:<citation_regex>)\s*(,|\.|\s)` -> `\1\2`
- Collapse consecutive commas and whitespace.

---

## 5. Audio Resolution Pipeline
1. **Watchtower MP3**:
   - Parse issue from article metadata/WOL URL (e.g., `pub-w26` + July -> `issue=202607`).
   - Query `https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS?output=json&pub=w&issue={issue}&fileformat=MP3&alllangs=0&langwritten={lang_written}&txtCMSLang={lang_written}`.
   - Match track by study article title or study date range.
2. **Bible Reading MP3**:
   - Query `https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS?output=json&pub=nwt&fileformat=MP3&alllangs=0&langwritten={lang_written}&txtCMSLang={lang_written}`.
   - Cached in memory on first load.
   - Lookup items matching `booknum == reading.book_number` and `track >= chapter_start and track <= chapter_end`.

---

## 6. Branding & Assets
New visual assets are supplied to ensure `ha-jw-library` is distinctly recognizable in HACS:
- `icon.png` (256x256), `icon@2x.png` (512x512)
- `logo.png` (256x256), `logo@2x.png` (512x512)
- Located in repository root and `custom_components/jw_library/`.

---

## 7. Testing Strategy
Unit tests in `tests/`:
- `test_api.py`: Verify parsing of meeting schedules, Watchtower articles, Bible chapters, citation cleanup, and CDN MP3 URL resolution.
- `test_coordinator.py`: Verify weekly interval calculations, rollovers, and error handling.
- `test_config_flow.py`: Verify language setup flow, options, and duplicate entry blocking.
- `test_sensor.py`: Verify sensor entity creation, state truncation, device info, and `extra_state_attributes`.
