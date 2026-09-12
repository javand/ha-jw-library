# Refactor BIBLE_BOOK_NAMES Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Extract `BIBLE_BOOK_NAMES` from `custom_components/jw_library/api.py` into a dedicated `custom_components/jw_library/bible_books.py` file, simplifying its representation and reducing line bloat in `api.py`.

**Architecture:**
- Create `custom_components/jw_library/bible_books.py` containing the `BIBLE_BOOK_NAMES` dictionary formatted cleanly and compactly.
- In `custom_components/jw_library/api.py`, import `BIBLE_BOOK_NAMES` from `.bible_books`.
- Re-export `BIBLE_BOOK_NAMES` from `api.py` for backward compatibility.
- Ensure all tests continue passing with zero regressions and zero linter errors.

**Global Constraints:**
- Zero external pip runtime dependencies.
- All 66 Bible books and their abbreviations must continue to map accurately.
- `api.py` imports must cleanly pass `ruff check .` and `ruff format --check .`.
- Full pytest test suite must pass 100%.

---

### Task 1: Extract BIBLE_BOOK_NAMES into `bible_books.py` and update `api.py`

**Files:**
- Create: `custom_components/jw_library/bible_books.py`
- Modify: `custom_components/jw_library/api.py`
- Modify: `tests/test_api.py`
- Create: `tests/test_bible_books.py`

**Interfaces:**
- Produces: `custom_components/jw_library/bible_books.py` exporting `BIBLE_BOOK_NAMES: dict[str, str]`
- Consumes: `api.py` importing `BIBLE_BOOK_NAMES` from `.bible_books`

- [ ] **Step 1: Write unit tests in `tests/test_bible_books.py`**
Verify `BIBLE_BOOK_NAMES` contains all expected book abbreviations and maps correctly.

- [ ] **Step 2: Create `custom_components/jw_library/bible_books.py`**
Define `BIBLE_BOOK_NAMES` compactly.

- [ ] **Step 3: Update `custom_components/jw_library/api.py`**
Replace the 70-line inline dictionary in `api.py` with:
`from .bible_books import BIBLE_BOOK_NAMES`

- [ ] **Step 4: Run tests and linters**
Run: `uv run pytest` and `uv run ruff check . && uv run ruff format --check .`
Expected: 44+ tests passing, 0 linter errors.

- [ ] **Step 5: Commit changes**
`git add custom_components/jw_library/ tests/`
`git commit -m "refactor: extract BIBLE_BOOK_NAMES to separate bible_books module"`
