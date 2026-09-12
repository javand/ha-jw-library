# Daily Text Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge the complete daily text functionality from `ha-jw-daily-text` into `ha-jw-library` under a single unified coordinator and "JW Library" device with 10 total sensors.

**Architecture:** Extend `JWLibraryApiClient` (`api.py`) with daily text scraping and scripture cleaning; update `JWLibraryData` with `daily_text: JWDailyTextData`; update `JWLibraryDataUpdateCoordinator` to manage unified updates; expose 6 dedicated daily text sensors in `sensor.py` alongside the 4 weekly study sensors.

**Tech Stack:** Python 3.13+, Home Assistant Custom Component SDK, aiohttp, pytest, pytest-homeassistant-custom-component, ruff.

**Spec:** `docs/superpowers/specs/2026-09-12-daily-text-integration-design.md`

## Global Constraints
- No external pip runtime dependencies beyond Home Assistant Core and Python standard library.
- Sensor names must NOT have the `"JW "` prefix (e.g. `Daily Text Today`, `Daily Text Today Comment`).
- State values for all sensors must be safely truncated to 255 characters using `truncate_state()`.
- Full untruncated scripture text and commentary must be stored on entity attributes (`text`) for TTS and dashboard usage.
- All code must pass `ruff check .` and `ruff format --check .` with zero errors.

---

### Task 1: Bible Citation Expansion & Commentary Cleaner (`api.py`)

**Files:**
- Modify: `custom_components/jw_library/api.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: Standard regex and HTML parsers
- Produces: 
  - `expand_bible_citation(citation: str) -> str`
  - `clean_commentary_scriptures(text: str) -> str`

- [ ] **Step 1: Write failing unit tests in `tests/test_api.py`**

```python
def test_clean_commentary_scriptures() -> None:
    """Test cleaning scripture citations from commentary text."""
    from custom_components.jw_library.api import clean_commentary_scriptures

    # Parenthetical citations
    raw = "We must show courage (Josh. 10:1; 2 Ki. 5:14) in all circumstances."
    cleaned = clean_commentary_scriptures(raw)
    assert "(Josh. 10:1; 2 Ki. 5:14)" not in cleaned
    assert "We must show courage in all circumstances." == cleaned

    # Comma-enclosed citations
    raw_comma = "Like David, 1 Sam. 17:45, we trust in Jehovah."
    assert clean_commentary_scriptures(raw_comma) == "Like David, we trust in Jehovah."


def test_expand_bible_citation() -> None:
    """Test expansion of abbreviated Bible citations."""
    from custom_components.jw_library.api import expand_bible_citation

    assert expand_bible_citation("Matt. 6:33") == "Matthew 6:33"
    assert expand_bible_citation("2 Ki. 5:14") == "2 Kings 5:14"
    assert expand_bible_citation("Ps. 23:1") == "Psalms 23:1"
```

- [ ] **Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_api.py -k "test_clean_commentary_scriptures or test_expand_bible_citation"`  
Expected: FAIL with `ImportError: cannot import name 'clean_commentary_scriptures'`

- [ ] **Step 3: Implement citation expander and commentary cleaner in `api.py`**

Add Bible book abbreviations and functions:
```python
BIBLE_BOOK_NAMES: dict[str, str] = {
    "gen": "Genesis", "ex": "Exodus", "lev": "Leviticus", "num": "Numbers",
    "deut": "Deuteronomy", "josh": "Joshua", "judg": "Judges", "ruth": "Ruth",
    "1 sam": "1 Samuel", "2 sam": "2 Samuel", "1 ki": "1 Kings", "2 ki": "2 Kings",
    "1 chron": "1 Chronicles", "2 chron": "2 Chronicles", "ezra": "Ezra", "neh": "Nehemiah",
    "esth": "Esther", "job": "Job", "ps": "Psalms", "prov": "Proverbs",
    "eccl": "Ecclesiastes", "song": "Song of Solomon", "isa": "Isaiah", "jer": "Jeremiah",
    "lam": "Lamentations", "ezek": "Ezekiel", "dan": "Daniel", "hos": "Hosea",
    "joel": "Joel", "amos": "Amos", "obad": "Obadiah", "jonah": "Jonah",
    "mic": "Micah", "nah": "Nahum", "hab": "Habakkuk", "zeph": "Zephaniah",
    "hag": "Haggai", "zech": "Zechariah", "mal": "Malachi", "matt": "Matthew",
    "mark": "Mark", "luke": "Luke", "john": "John", "acts": "Acts",
    "rom": "Romans", "1 cor": "1 Corinthians", "2 cor": "2 Corinthians", "gal": "Galatians",
    "eph": "Ephesians", "phil": "Philippians", "col": "Colossians", "1 thess": "1 Thessalonians",
    "2 thess": "2 Thessalonians", "1 tim": "1 Timothy", "2 tim": "2 Timothy", "titus": "Titus",
    "philem": "Philemon", "heb": "Hebrews", "jas": "James", "1 pet": "1 Peter",
    "2 pet": "2 Peter", "1 john": "1 John", "2 john": "2 John", "3 john": "3 John",
    "jude": "Jude", "rev": "Revelation",
}

def expand_bible_citation(citation: str) -> str:
    """Expand abbreviated book citation like 'Matt. 6:33' to 'Matthew 6:33'."""
    cleaned = citation.strip()
    match = re.match(r"^([1-3]?\s*[A-Za-z]+)\.?\s*(.*)$", cleaned)
    if not match:
        return cleaned
    book_part = match.group(1).strip().lower().rstrip(".")
    remainder = match.group(2).strip()
    expanded = BIBLE_BOOK_NAMES.get(book_part, book_part.title())
    return f"{expanded} {remainder}".strip()

def clean_commentary_scriptures(text: str) -> str:
    """Remove inline scripture citations from commentary text for fluent TTS reading."""
    if not text:
        return text
    books = sorted(
        list(BIBLE_BOOK_NAMES.keys()) + list(set(BIBLE_BOOK_NAMES.values())),
        key=len,
        reverse=True,
    )
    books_pattern = "|".join(re.escape(b) for b in books)
    dash_range = r"[\u2013-]"
    sub_cite = r"(?:(?:" + books_pattern + r")\s+)?\d+:\d+(?:" + dash_range + r"\d+)?"
    citation_regex = (
        r"(?:" + books_pattern + r")\s+\d+:\d+(?:" + dash_range + r"\d+)?"
        r"(?:,\s*\d+)*(?:\s*;\s*" + sub_cite + r"(?:,\s*\d+)*)*"
    )

    paren_regex = r"\s*\(\s*(?:[Rr]ead\s+)?(?:" + citation_regex + r")\.?\s*\)"
    text = re.sub(paren_regex, "", text)

    comma_regex = r",\s*(?:" + citation_regex + r")\s*,"
    text = re.sub(comma_regex, ",", text)

    text = re.sub(
        r"([\"'\w]),\s*(?:" + citation_regex + r")\s*(,|\.|\s)",
        r"\1\2",
        text,
    )

    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_api.py -k "test_clean_commentary_scriptures or test_expand_bible_citation"`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add custom_components/jw_library/api.py tests/test_api.py
git commit -m "feat: add Bible citation expansion and commentary scripture cleaning"
```

---

### Task 2: Daily Text Data Classes & Scraper Methods (`api.py`)

**Files:**
- Modify: `custom_components/jw_library/api.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `_async_fetch_text` from `JWLibraryApiClient`
- Produces:
  - `DailyTextEntry` dataclass
  - `JWDailyTextData` dataclass
  - `JWLibraryData.daily_text: JWDailyTextData`
  - `async_get_daily_text_entry(self, date_val: datetime.date) -> DailyTextEntry`
  - `async_get_daily_text_data(self, today_date: datetime.date) -> JWDailyTextData`

- [ ] **Step 1: Write failing unit test for daily text fetching & parsing in `tests/test_api.py`**

```python
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
```

- [ ] **Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_api.py -k "test_parse_daily_text_page"`  
Expected: FAIL with `AttributeError: 'JWLibraryApiClient' object has no attribute '_parse_daily_text_html'`

- [ ] **Step 3: Implement data models and scraping methods in `api.py`**

1. Define `DailyTextEntry` and `JWDailyTextData`:
```python
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
```

2. Update `JWLibraryData`:
```python
@dataclass
class JWLibraryData:
    """Consolidated study data for coordinator."""
    this_week: WeeklyStudyData
    next_week: WeeklyStudyData
    daily_text: JWDailyTextData
```

3. Implement `_parse_daily_text_html(self, date_str: str, html: str) -> DailyTextEntry`:
```python
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
            raw_citation = parts[1].strip()
            scripture_citation = expand_bible_citation(raw_citation)
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
```

4. Implement `async_get_daily_text_entry` and `async_get_daily_text_data`:
```python
async def async_get_daily_text_entry(self, date_val: datetime.date) -> DailyTextEntry:
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
```

5. Update `async_get_library_data`:
```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_api.py -k "test_parse_daily_text_page"`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add custom_components/jw_library/api.py tests/test_api.py
git commit -m "feat: implement daily text scraping and data models in API client"
```

---

### Task 3: Coordinator Integration & Test Updates (`coordinator.py` & `tests/test_coordinator.py`)

**Files:**
- Modify: `tests/test_coordinator.py`
- Modify: `tests/test_api.py`
- Verify: `custom_components/jw_library/coordinator.py`

**Interfaces:**
- Consumes: `JWLibraryData` with `daily_text` attribute
- Produces: Green coordinator tests with unified payload

- [ ] **Step 1: Update sample data fixture in `tests/test_coordinator.py`**

In `tests/test_coordinator.py`, update `_sample_library_data()`:
```python
def _sample_daily_text_data() -> JWDailyTextData:
    return JWDailyTextData(
        yesterday=DailyTextEntry(
            date="2026-09-09",
            day_and_date="Wednesday, September 9",
            scripture_text="Yesterday scripture",
            scripture="Proverbs 3:5",
            comments="Yesterday commentary",
        ),
        today=DailyTextEntry(
            date="2026-09-10",
            day_and_date="Thursday, September 10",
            scripture_text="Today scripture",
            scripture="Matthew 6:33",
            comments="Today commentary",
        ),
        tomorrow=DailyTextEntry(
            date="2026-09-11",
            day_and_date="Friday, September 11",
            scripture_text="Tomorrow scripture",
            scripture="Psalms 23:1",
            comments="Tomorrow commentary",
        ),
    )
```
Include `daily_text=_sample_daily_text_data()` when constructing `JWLibraryData`.

- [ ] **Step 2: Run coordinator tests**

Run: `uv run pytest tests/test_coordinator.py`  
Expected: All tests PASS.

- [ ] **Step 3: Update `test_api_client_network_calls` in `tests/test_api.py`**

Add mock response handling for daily text URL pattern (`"/dt/r1/"`) in `test_api_client_network_calls` returning sample daily text HTML, and assert `data.daily_text.today.scripture == "Matthew 6:33"`.

- [ ] **Step 4: Run all API tests**

Run: `uv run pytest tests/test_api.py`  
Expected: All tests PASS.

- [ ] **Step 5: Commit changes**

```bash
git add tests/test_coordinator.py tests/test_api.py
git commit -m "test: update coordinator and API client test fixtures for daily text data"
```

---

### Task 4: Daily Text Sensor Entities (`sensor.py` & `tests/test_sensor.py`)

**Files:**
- Modify: `custom_components/jw_library/sensor.py`
- Modify: `tests/test_sensor.py`

**Interfaces:**
- Consumes: `JWLibraryEntity` and `DailyTextEntry` from coordinator
- Produces: 6 new sensor entities (`Daily Text Today`, `Daily Text Today Comment`, `Daily Text Yesterday`, `Daily Text Yesterday Comment`, `Daily Text Tomorrow`, `Daily Text Tomorrow Comment`)

- [ ] **Step 1: Write failing unit test in `tests/test_sensor.py`**

```python
def test_daily_text_sensor_state_and_attributes() -> None:
    """Test daily text sensor state and attribute exposure."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test_entry")
    coordinator = MagicMock()
    coordinator.config_entry = entry
    coordinator.data = _sample_library_data()

    sensor_text = JWDailyTextSensor(
        coordinator=coordinator,
        target_day="today",
        field_type="text",
        name="Daily Text Today",
        unique_id="test_entry_daily_text_today",
    )
    assert sensor_text.native_value == "Today scripture"
    assert sensor_text.extra_state_attributes["scripture"] == "Matthew 6:33"
    assert sensor_text.extra_state_attributes["date"] == "2026-09-10"
    assert sensor_text.icon == "mdi:book-open-variant"

    sensor_comment = JWDailyTextSensor(
        coordinator=coordinator,
        target_day="today",
        field_type="comment",
        name="Daily Text Today Comment",
        unique_id="test_entry_daily_text_today_comment",
    )
    assert sensor_comment.native_value == "Today commentary"
    assert sensor_comment.icon == "mdi:comment-text-outline"
```

- [ ] **Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_sensor.py -k "test_daily_text_sensor_state_and_attributes"`  
Expected: FAIL with `ImportError: cannot import name 'JWDailyTextSensor'`

- [ ] **Step 3: Implement `JWDailyTextSensor` and register entities in `sensor.py`**

1. Define `JWDailyTextSensor(JWLibraryEntity, SensorEntity)`:
```python
class JWDailyTextSensor(JWLibraryEntity, SensorEntity):
    """Representation of a JW Daily Text sensor."""

    def __init__(
        self,
        coordinator: JWLibraryDataUpdateCoordinator,
        target_day: str,
        field_type: str,
        name: str,
        unique_id: str,
    ) -> None:
        """Initialize the daily text sensor."""
        super().__init__(coordinator, unique_id)
        self._target_day = target_day
        self._field_type = field_type
        self._attr_name = name
        self._attr_icon = (
            "mdi:book-open-variant"
            if field_type == "text"
            else "mdi:comment-text-outline"
        )

    @property
    def _entry_data(self) -> DailyTextEntry | None:
        """Return DailyTextEntry for target day."""
        if self.coordinator.data is None or self.coordinator.data.daily_text is None:
            return None
        return getattr(self.coordinator.data.daily_text, self._target_day, None)

    @property
    def native_value(self) -> str | None:
        """Return scripture or comment truncated to 255 chars."""
        entry = self._entry_data
        if entry is None:
            return None
        val = entry.scripture_text if self._field_type == "text" else entry.comments
        return truncate_state(val) if val else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return full untruncated text and date attributes."""
        entry = self._entry_data
        if entry is None:
            return {}
        if self._field_type == "text":
            return {
                "text": entry.scripture_text,
                "scripture": entry.scripture,
                "day_and_date": entry.day_and_date,
                "date": entry.date,
            }
        return {
            "text": entry.comments,
            "day_and_date": entry.day_and_date,
            "date": entry.date,
        }
```

2. In `async_setup_entry`, append the 6 daily text sensors:
```python
        JWDailyTextSensor(
            coordinator=coordinator,
            target_day="today",
            field_type="text",
            name="Daily Text Today",
            unique_id=f"{entry_id}_daily_text_today",
        ),
        JWDailyTextSensor(
            coordinator=coordinator,
            target_day="today",
            field_type="comment",
            name="Daily Text Today Comment",
            unique_id=f"{entry_id}_daily_text_today_comment",
        ),
        JWDailyTextSensor(
            coordinator=coordinator,
            target_day="yesterday",
            field_type="text",
            name="Daily Text Yesterday",
            unique_id=f"{entry_id}_daily_text_yesterday",
        ),
        JWDailyTextSensor(
            coordinator=coordinator,
            target_day="yesterday",
            field_type="comment",
            name="Daily Text Yesterday Comment",
            unique_id=f"{entry_id}_daily_text_yesterday_comment",
        ),
        JWDailyTextSensor(
            coordinator=coordinator,
            target_day="tomorrow",
            field_type="text",
            name="Daily Text Tomorrow",
            unique_id=f"{entry_id}_daily_text_tomorrow",
        ),
        JWDailyTextSensor(
            coordinator=coordinator,
            target_day="tomorrow",
            field_type="comment",
            name="Daily Text Tomorrow Comment",
            unique_id=f"{entry_id}_daily_text_tomorrow_comment",
        ),
```

- [ ] **Step 4: Update `test_sensor_async_setup_entry` in `tests/test_sensor.py`**

Assert that `len(added_entities) == 10`, and check that all 6 daily text sensor names are in `[s._attr_name for s in added_entities]`.

- [ ] **Step 5: Run all sensor tests**

Run: `uv run pytest tests/test_sensor.py`  
Expected: All tests PASS.

- [ ] **Step 6: Commit changes**

```bash
git add custom_components/jw_library/sensor.py tests/test_sensor.py
git commit -m "feat: implement 6 Daily Text sensor entities in sensor platform"
```

---

### Task 5: Documentation, Linters & Live Verification

**Files:**
- Modify: `README.md`
- Scratch script: `scratch/smoke_test_combined.py`

**Interfaces:**
- Consumes: All 10 sensors and live WOL endpoint
- Produces: Updated documentation, 0 linter errors, verified live data retrieval

- [ ] **Step 1: Update `README.md`**

Add Daily Text features and entity descriptions to the sensors table:
- `sensor.jw_library_daily_text_today`
- `sensor.jw_library_daily_text_today_comment`
- `sensor.jw_library_daily_text_yesterday`
- `sensor.jw_library_daily_text_yesterday_comment`
- `sensor.jw_library_daily_text_tomorrow`
- `sensor.jw_library_daily_text_tomorrow_comment`
Add example automation: Daily Text TTS morning announcement.

- [ ] **Step 2: Run linters and formatting**

Run: `uv run ruff check . && uv run ruff format --check .`  
Expected: 0 errors, all formatted.

- [ ] **Step 3: Run entire pytest test suite with coverage**

Run: `uv run pytest --cov=custom_components/jw_library tests/`  
Expected: 100% pass, high test coverage.

- [ ] **Step 4: Run live smoke test**

Run a script that fetches both weekly study and daily text (yesterday, today, tomorrow) from live `wol.jw.org` to confirm real data parses cleanly.

- [ ] **Step 5: Commit documentation and finalize**

```bash
git add README.md
git commit -m "docs: update README with Daily Text features, sensors, and automations"
```
