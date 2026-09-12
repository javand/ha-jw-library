"""Sensor platform for jw_library."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .entity import JWLibraryEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .api import (
        BibleReadingEntry,
        DailyTextEntry,
        WatchtowerArticle,
        WeeklyStudyData,
    )
    from .coordinator import JWLibraryDataUpdateCoordinator
    from .data import JWLibraryConfigEntry


def truncate_state(value: str, max_len: int = 255) -> str:
    """Truncate string to max length for HA state."""
    if len(value) <= max_len:
        return value
    if max_len <= 1:
        return value[:max_len]
    return value[: max_len - 1] + "…"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JWLibraryConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: JWLibraryDataUpdateCoordinator = (
        entry.runtime_data.coordinator
        if hasattr(entry.runtime_data, "coordinator")
        else entry.runtime_data
    )

    entry_id = getattr(entry, "entry_id", DOMAIN)

    # Migrate any legacy entity IDs with duplicate 'jw_' prefix
    ent_reg = er.async_get(hass)
    for entity_entry in er.async_entries_for_config_entry(ent_reg, entry_id):
        if (
            entity_entry.domain == "sensor"
            and "sensor.jw_library_jw_" in entity_entry.entity_id
        ):
            new_entity_id = entity_entry.entity_id.replace(
                "sensor.jw_library_jw_", "sensor.jw_library_"
            )
            if not ent_reg.async_is_registered(new_entity_id):
                ent_reg.async_update_entity(
                    entity_entry.entity_id,
                    new_entity_id=new_entity_id,
                )

    sensors = [
        JWWatchtowerSensor(
            coordinator=coordinator,
            target_week="this_week",
            name="Watchtower This Week",
            unique_id=f"{entry_id}_watchtower_this_week",
            icon="mdi:book-open-page-variant",
        ),
        JWWatchtowerSensor(
            coordinator=coordinator,
            target_week="next_week",
            name="Watchtower Next Week",
            unique_id=f"{entry_id}_watchtower_next_week",
            icon="mdi:book-open-page-variant-outline",
        ),
        JWBibleReadingSensor(
            coordinator=coordinator,
            target_week="this_week",
            name="Bible Reading This Week",
            unique_id=f"{entry_id}_bible_reading_this_week",
            icon="mdi:book-open-variant",
        ),
        JWBibleReadingSensor(
            coordinator=coordinator,
            target_week="next_week",
            name="Bible Reading Next Week",
            unique_id=f"{entry_id}_bible_reading_next_week",
            icon="mdi:book-open-variant",
        ),
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
    ]

    async_add_entities(sensors)


class JWWatchtowerSensor(JWLibraryEntity, SensorEntity):
    """Representation of a Watchtower Study sensor."""

    def __init__(
        self,
        coordinator: JWLibraryDataUpdateCoordinator,
        target_week: str,
        name: str,
        unique_id: str,
        icon: str,
    ) -> None:
        """Initialize the Watchtower sensor."""
        super().__init__(coordinator, unique_id=unique_id)
        self._target_week = target_week
        self._attr_name = name
        self._attr_icon = icon

    @property
    def _week_data(self) -> WeeklyStudyData | None:
        """Return the WeeklyStudyData for this sensor."""
        if self.coordinator.data is None:
            return None
        return getattr(self.coordinator.data, self._target_week, None)

    @property
    def _article(self) -> WatchtowerArticle | None:
        """Return the WatchtowerArticle for this sensor."""
        week = self._week_data
        return week.watchtower if week else None

    @property
    def native_value(self) -> str | None:
        """Return article title truncated to 255 chars."""
        article = self._article
        if article is None or not article.title:
            return None
        return truncate_state(article.title)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        article = self._article
        if article is None:
            return {}

        return {
            "title": article.title,
            "date_range": article.date_range,
            "theme_scripture": article.theme_scripture,
            "songs": article.songs,
            "audio_url": article.audio_url,
            "text": article.text,
            "issue": article.issue,
            "doc_id": article.doc_id,
        }


class JWBibleReadingSensor(JWLibraryEntity, SensorEntity):
    """Representation of a Bible Reading sensor."""

    def __init__(
        self,
        coordinator: JWLibraryDataUpdateCoordinator,
        target_week: str,
        name: str,
        unique_id: str,
        icon: str,
    ) -> None:
        """Initialize the Bible reading sensor."""
        super().__init__(coordinator, unique_id=unique_id)
        self._target_week = target_week
        self._attr_name = name
        self._attr_icon = icon

    @property
    def _week_data(self) -> WeeklyStudyData | None:
        """Return the WeeklyStudyData for this sensor."""
        if self.coordinator.data is None:
            return None
        return getattr(self.coordinator.data, self._target_week, None)

    @property
    def _reading(self) -> BibleReadingEntry | None:
        """Return the BibleReadingEntry for this sensor."""
        week = self._week_data
        return week.bible_reading if week else None

    @property
    def native_value(self) -> str | None:
        """Return Bible reading citation truncated to 255 chars."""
        reading = self._reading
        if reading is None or not reading.citation:
            return None
        return truncate_state(reading.citation)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        reading = self._reading
        if reading is None:
            return {}

        return {
            "citation": reading.citation,
            "book_name": reading.book_name,
            "book_number": reading.book_number,
            "chapter_start": reading.chapter_start,
            "chapter_end": reading.chapter_end,
            "audio_url": reading.audio_url,
            "audio_urls": reading.audio_urls,
            "text": reading.text,
            "doc_id": reading.doc_id,
        }


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
