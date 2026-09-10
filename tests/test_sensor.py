"""Unit tests for JW Library sensor platform."""

from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jw_library.const import DOMAIN
from custom_components.jw_library.sensor import (
    JWBibleReadingSensor,
    JWWatchtowerSensor,
    async_setup_entry,
    truncate_state,
)
from tests.test_coordinator import _sample_library_data


def test_truncate_state() -> None:
    """Test truncate_state utility."""
    short = "Short string"
    assert truncate_state(short, 255) == short

    long_str = "a" * 300
    truncated = truncate_state(long_str, 255)
    assert len(truncated) == 255
    assert truncated.endswith("…")


@pytest.mark.asyncio
async def test_sensor_async_setup_entry(hass: HomeAssistant) -> None:
    """Test setting up all sensors via async_setup_entry."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test_entry")
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.config_entry = entry
    coordinator.data = _sample_library_data()

    entry.runtime_data = MagicMock()
    entry.runtime_data.coordinator = coordinator

    added_entities = []

    def async_add_entities(entities: list) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, entry, async_add_entities)

    assert len(added_entities) == 4
    names = [s._attr_name for s in added_entities]
    assert "JW Watchtower This Week" in names
    assert "JW Watchtower Next Week" in names
    assert "JW Bible Reading This Week" in names
    assert "JW Bible Reading Next Week" in names


def test_watchtower_sensor_state_and_attributes() -> None:
    """Test Watchtower sensor state and attribute exposure."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test_entry")
    coordinator = MagicMock()
    coordinator.config_entry = entry
    coordinator.data = _sample_library_data()

    sensor = JWWatchtowerSensor(
        coordinator=coordinator,
        target_week="this_week",
        name="JW Watchtower This Week",
        unique_id="test_entry_watchtower_this_week",
        icon="mdi:book-open-page-variant",
    )

    assert sensor.native_value == "Learn From the Gibeonites"
    attrs = sensor.extra_state_attributes
    assert attrs["title"] == "Learn From the Gibeonites"
    assert attrs["date_range"] == "September 7-13, 2026"
    assert attrs["theme_scripture"] == "Josh. 10:1"
    assert attrs["songs"] == ["Song 88"]
    assert attrs["audio_url"] == "https://example.com/wt.mp3"
    assert attrs["text"] == "Full text"
    assert attrs["issue"] == "202607"
    assert attrs["doc_id"] == "2026482"
    assert sensor.unique_id == "test_entry_watchtower_this_week"
    assert sensor.device_info is not None

    # Test coordinator data is None
    coordinator.data = None
    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


def test_bible_reading_sensor_state_and_attributes() -> None:
    """Test Bible reading sensor state and attribute exposure."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test_entry")
    coordinator = MagicMock()
    coordinator.config_entry = entry
    coordinator.data = _sample_library_data()

    sensor = JWBibleReadingSensor(
        coordinator=coordinator,
        target_week="this_week",
        name="JW Bible Reading This Week",
        unique_id="test_entry_bible_reading_this_week",
        icon="mdi:book-open-variant",
    )

    assert sensor.native_value == "JEREMIAH 32-33"
    attrs = sensor.extra_state_attributes
    assert attrs["citation"] == "JEREMIAH 32-33"
    assert attrs["book_name"] == "Jeremiah"
    assert attrs["book_number"] == 24
    assert attrs["chapter_start"] == 32
    assert attrs["chapter_end"] == 33
    assert attrs["audio_url"] == "https://example.com/ch32.mp3"
    assert len(attrs["audio_urls"]) == 2
    assert attrs["audio_urls"][0]["chapter"] == 32
    assert attrs["audio_urls"][1]["chapter"] == 33
    assert attrs["text"] == "Bible reading text"
    assert attrs["doc_id"] == "202026252"
    assert sensor.unique_id == "test_entry_bible_reading_this_week"

    # Test coordinator data is None
    coordinator.data = None
    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}
