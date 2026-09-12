# Design Specification: Merging Daily Text into JW Library

**Date**: 2026-09-12  
**Status**: Approved  
**Author**: Antigravity & User  
**Target Repository**: `javand/ha-jw-library`

---

## 1. Overview & Objective

Combine the capabilities of `ha-jw-daily-text` directly into `ha-jw-library`. Rather than running two separate custom integrations in Home Assistant, `jw_library` will serve as the single, all-in-one integration providing both:
1. **Weekly Study Material**: Watchtower study article text & direct CDN audio, and Life & Ministry meeting Bible reading text & direct CDN multi-chapter audio.
2. **Daily Text Material**: Yesterday, Today, and Tomorrow's daily scripture text and commentary, cleaned of inline scripture references for natural Text-to-Speech (TTS) reading.

All 10 sensors reside under a single unified Home Assistant device (**JW Library**).

---

## 2. Architecture & Data Model

### 2.1 Dataclasses (`api.py`)

```python
@dataclass
class DailyTextEntry:
    """Data model for a single day's daily text."""
    date: str  # Format: 'YYYY-MM-DD'
    day_and_date: str  # Format: 'Friday, September 11'
    scripture_text: str  # Verse text
    scripture: str  # Expanded citation (e.g. 'Matthew 6:33')
    comments: str  # Commentary with citations cleaned for TTS

@dataclass
class JWDailyTextData:
    """Container for 3-day daily text window."""
    yesterday: DailyTextEntry
    today: DailyTextEntry
    tomorrow: DailyTextEntry

@dataclass
class JWLibraryData:
    """Unified payload managed by coordinator."""
    this_week: WeeklyStudyData
    next_week: WeeklyStudyData
    daily_text: JWDailyTextData
```

### 2.2 API Scraping & Parsing (`api.py`)

1. **Bible Citation Expansion**:
   - Port book abbreviation mappings (e.g. `Matt.` -> `Matthew`, `2 Ki.` -> `2 Kings`) and regex expander function `expand_bible_citation(citation: str) -> str`.
2. **Commentary Cleaning**:
   - Port `clean_commentary_scriptures(text: str) -> str`:
     - Strips parenthetical scripture citations: `(2 Ki. 5:14)` or `(Read 2 Kings 5:14)`.
     - Strips comma-delimited scripture references: `, 2 Ki. 5:14,`.
     - Strips trailing publication references: `w24.06 10 ¶7`.
3. **Endpoint Requests**:
   - `async_get_daily_text_entry(date_val: datetime.date) -> DailyTextEntry`:
     Queries `https://wol.jw.org/{lang_prefix}/wol/dt/r1/{self._language}/{year}/{month:02d}/{day:02d}`.
     Parses `<h2...>` for `day_and_date`, `<p class="themeScrp"...>` for `scripture_text` and citation, and `<div class="bodyTxt"...>` for `comments`.
   - `async_get_daily_text_data(today_date: datetime.date) -> JWDailyTextData`:
     Queries yesterday, today, and tomorrow in parallel via `asyncio.gather`.
4. **Unified Fetch**:
   - `async_get_library_data(base_date)` executes `asyncio.gather(this_week, next_week, daily_text)` to fetch all required weekly and daily information in a single round-trip cycle.

---

## 3. Coordinator & Lifecycle (`coordinator.py`)

- Managed by `JWLibraryDataUpdateCoordinator` (`DataUpdateCoordinator[JWLibraryData]`).
- **Interval**: 12-hour periodic refresh with exponential backoff on network failures.
- **Midnight Rollover**: Synchronized local midnight rollover timer (`async_track_point_in_time` at `00:00:05` local time).
- At midnight, both the weekly study articles and the rolling 3-day daily text window automatically refresh and update all entities simultaneously.

---

## 4. Entities & Sensors (`sensor.py`)

All sensors share the unified base class `JWLibraryEntity` and attach to the single **JW Library** device.

### 4.1 Sensor List (10 Entities)

1. `sensor.jw_library_watchtower_this_week`: **Watchtower This Week**
2. `sensor.jw_library_watchtower_next_week`: **Watchtower Next Week**
3. `sensor.jw_library_bible_reading_this_week`: **Bible Reading This Week**
4. `sensor.jw_library_bible_reading_next_week`: **Bible Reading Next Week**
5. `sensor.jw_library_daily_text_today`: **Daily Text Today**
   - Icon: `mdi:book-open-variant`
   - State: Scripture text (truncated to 255 chars)
   - Attributes: `text` (full untruncated verse), `scripture`, `day_and_date`, `date`
6. `sensor.jw_library_daily_text_today_comment`: **Daily Text Today Comment**
   - Icon: `mdi:comment-text-outline`
   - State: Commentary text (truncated to 255 chars)
   - Attributes: `text` (full untruncated commentary), `day_and_date`, `date`
7. `sensor.jw_library_daily_text_yesterday`: **Daily Text Yesterday**
   - Icon: `mdi:book-open-variant`
   - State: Scripture text (truncated to 255 chars)
   - Attributes: `text`, `scripture`, `day_and_date`, `date`
8. `sensor.jw_library_daily_text_yesterday_comment`: **Daily Text Yesterday Comment**
   - Icon: `mdi:comment-text-outline`
   - State: Commentary text (truncated to 255 chars)
   - Attributes: `text`, `day_and_date`, `date`
9. `sensor.jw_library_daily_text_tomorrow`: **Daily Text Tomorrow**
   - Icon: `mdi:book-open-variant`
   - State: Scripture text (truncated to 255 chars)
   - Attributes: `text`, `scripture`, `day_and_date`, `date`
10. `sensor.jw_library_daily_text_tomorrow_comment`: **Daily Text Tomorrow Comment**
    - Icon: `mdi:comment-text-outline`
    - State: Commentary text (truncated to 255 chars)
    - Attributes: `text`, `day_and_date`, `date`

---

## 5. Testing & Verification

1. **Unit Tests**:
   - `test_api.py`: Test `clean_commentary_scriptures`, `expand_bible_citation`, daily text HTML parsing, and `async_get_daily_text_data`.
   - `test_coordinator.py`: Test coordinator update handling `JWLibraryData` with daily text included.
   - `test_sensor.py`: Test setup and attribute resolution for all 10 sensors.
2. **Linter & Formatting**:
   - Run `ruff check .` and `ruff format --check .`.
3. **Live Verification**:
   - Run live smoke test fetching today, yesterday, and tomorrow from WOL to verify live payload.
