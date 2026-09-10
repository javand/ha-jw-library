# JW Library Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Home Assistant HACS integration (`jw_library`) that scrapes the weekly Watchtower study article and Bible reading from `wol.jw.org` and queries official JW CDN APIs for direct MP3 streaming to Google Cast/Audio devices.

**Architecture:** A coordinator-driven integration with an asynchronous API client (`JWLibraryApiClient`) that scrapes WOL for meeting schedules and cleans article text for natural TTS narration, while querying the JW CDN `GETPUBMEDIALINKS` endpoint for official high-quality MP3 streams.

**Tech Stack:** Python 3.12+, Home Assistant Core integration API, aiohttp, pytest, ruff.

**Spec:** `docs/superpowers/specs/2026-09-10-jw-library-design.md`

## Global Constraints

- Domain name: `jw_library` in `custom_components/jw_library/`.
- Home Assistant minimum version: `2024.6.0+`.
- Zero additional external dependencies (standard HA aiohttp and python stdlib).
- 100% test coverage matching `ha-jw-daily-text` across API, Coordinator, Config Flow, and Sensors.
- Native Home Assistant constructs; entity IDs use stable device-linked identifiers.

---

### Task 1: Scaffolding, Domain Constants, and Data Types

**Files:**
- Create: `custom_components/jw_library/__init__.py`
- Create: `custom_components/jw_library/const.py`
- Create: `custom_components/jw_library/data.py`
- Create: `custom_components/jw_library/manifest.json`
- Create: `custom_components/jw_library/strings.json`
- Create: `custom_components/jw_library/translations/en.json`
- Modify: `hacs.json`
- Delete: `custom_components/integration_blueprint/` (remove boilerplate)
- Test: `tests/test_const.py`

**Interfaces:**
- Produces: `DOMAIN = "jw_library"`, language codes, `JWLibraryConfigEntry = ConfigEntry[JWLibraryData]`.

- [ ] **Step 1: Write failing test in `tests/test_const.py`**
- [ ] **Step 2: Create `const.py`, `data.py`, `manifest.json`, `strings.json`, and `translations/en.json`**
- [ ] **Step 3: Update `hacs.json` to name `JW Library`**
- [ ] **Step 4: Remove template `custom_components/integration_blueprint` directory**
- [ ] **Step 5: Run tests and verify they pass**
- [ ] **Step 6: Commit changes**

---

### Task 2: API Client & Data Parsing (`api.py`)

**Files:**
- Create: `custom_components/jw_library/api.py`
- Test: `tests/test_api.py`
- Fixtures: `tests/fixtures/meetings_sample.html`, `tests/fixtures/watchtower_sample.html`, `tests/fixtures/workbook_sample.html`, `tests/fixtures/bible_chapter_sample.html`

**Interfaces:**
- Consumes: `aiohttp.ClientSession`, language codes from `const.py`.
- Produces: `WatchtowerArticle`, `BibleReadingEntry`, `WeeklyStudyData`, `JWLibraryData`, `JWLibraryApiClient`.
- Key Methods:
  - `clean_tts_scriptures(text: str) -> str`: strips parentheses and comma citations.
  - `async_get_weekly_data(target_date: datetime.date) -> WeeklyStudyData`
  - `async_get_library_data() -> JWLibraryData` (fetches `this_week` and `next_week`)

- [ ] **Step 1: Write unit tests in `tests/test_api.py` testing HTML scraping, citation regex cleanup, and CDN audio resolution with mock aiohttp responses**
- [ ] **Step 2: Run `pytest tests/test_api.py` to confirm failure**
- [ ] **Step 3: Implement `JWLibraryApiClient`, HTML strippers, and `GETPUBMEDIALINKS` queries in `custom_components/jw_library/api.py`**
- [ ] **Step 4: Run `pytest tests/test_api.py` to confirm 100% pass**
- [ ] **Step 5: Commit changes**

---

### Task 3: Data Coordinator (`coordinator.py`) & Lifecycle (`__init__.py`)

**Files:**
- Create: `custom_components/jw_library/coordinator.py`
- Modify: `custom_components/jw_library/__init__.py`
- Test: `tests/test_coordinator.py`

**Interfaces:**
- Consumes: `JWLibraryApiClient` from `api.py`.
- Produces: `JWLibraryDataUpdateCoordinator` managing 12-hour polling and updating `coordinator.data`.

- [ ] **Step 1: Write coordinator tests in `tests/test_coordinator.py`**
- [ ] **Step 2: Run `pytest tests/test_coordinator.py` to confirm failure**
- [ ] **Step 3: Implement `JWLibraryDataUpdateCoordinator` in `coordinator.py` and entry setup/unload in `__init__.py`**
- [ ] **Step 4: Run `pytest tests/test_coordinator.py` to confirm pass**
- [ ] **Step 5: Commit changes**

---

### Task 4: Config Flow (`config_flow.py`)

**Files:**
- Create: `custom_components/jw_library/config_flow.py`
- Test: `tests/test_config_flow.py`

**Interfaces:**
- Consumes: `DOMAIN`, `CONF_LANGUAGE` from `const.py`.
- Produces: `JWLibraryConfigFlowHandler` with language selection step and options flow.

- [ ] **Step 1: Write config flow tests in `tests/test_config_flow.py`**
- [ ] **Step 2: Run `pytest tests/test_config_flow.py` to confirm failure**
- [ ] **Step 3: Implement config flow with language dropdown and duplicate check**
- [ ] **Step 4: Run `pytest tests/test_config_flow.py` and confirm pass**
- [ ] **Step 5: Commit changes**

---

### Task 5: Entity Platform & Sensors (`sensor.py`, `entity.py`)

**Files:**
- Create: `custom_components/jw_library/entity.py`
- Create: `custom_components/jw_library/sensor.py`
- Test: `tests/test_sensor.py`

**Interfaces:**
- Consumes: `JWLibraryDataUpdateCoordinator`, `WeeklyStudyData`.
- Produces:
  - `sensor.jw_watchtower_this_week`
  - `sensor.jw_watchtower_next_week`
  - `sensor.jw_bible_reading_this_week`
  - `sensor.jw_bible_reading_next_week`

- [ ] **Step 1: Write sensor tests in `tests/test_sensor.py` verifying state titles, full text, and `audio_url`/`audio_urls` attribute schemas**
- [ ] **Step 2: Run `pytest tests/test_sensor.py` to confirm failure**
- [ ] **Step 3: Implement base entity in `entity.py` and sensors in `sensor.py`**
- [ ] **Step 4: Run `pytest tests/test_sensor.py` to confirm pass**
- [ ] **Step 5: Commit changes**

---

### Task 6: Visual Assets & Icon Branding

**Files:**
- Create: `icon.png` (256x256)
- Create: `icon@2x.png` (512x512)
- Create: `logo.png` (256x256)
- Create: `logo@2x.png` (512x512)
- Create: `custom_components/jw_library/icon.png`, etc.

- [ ] **Step 1: Create distinctive branding graphics for JW Library (Watchtower & Bible with audio streaming wave motif)**
- [ ] **Step 2: Save assets in repository root and `custom_components/jw_library/`**
- [ ] **Step 3: Commit assets**

---

### Task 7: Full Integration Verification & Ruff Linting

**Files:**
- All integration and test files.

- [ ] **Step 1: Run full test suite with coverage (`pytest tests/ --cov=custom_components/jw_library`)**
- [ ] **Step 2: Run ruff linter and formatter (`ruff check .` and `ruff format --check .`)**
- [ ] **Step 3: Validate against live endpoints using end-to-end smoke verification test**
- [ ] **Step 4: Final commit and prepare walkthrough**
