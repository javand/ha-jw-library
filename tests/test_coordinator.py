"""Unit tests for JWLibraryDataUpdateCoordinator."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jw_library.api import (
    BibleReadingEntry,
    JWLibraryApiClient,
    JWLibraryApiClientCommunicationError,
    JWLibraryApiClientError,
    JWLibraryData,
    WatchtowerArticle,
    WeeklyStudyData,
)
from custom_components.jw_library.const import DOMAIN
from custom_components.jw_library.coordinator import (
    JWLibraryDataUpdateCoordinator,
)


def _sample_library_data() -> JWLibraryData:
    """Return dummy JWLibraryData for testing."""
    wt = WatchtowerArticle(
        title="Learn From the Gibeonites",
        date_range="September 7-13, 2026",
        theme_scripture="Josh. 10:1",
        songs=["Song 88"],
        audio_url="https://example.com/wt.mp3",
        text="Full text",
        issue="202607",
        doc_id="2026482",
    )
    br = BibleReadingEntry(
        citation="JEREMIAH 32-33",
        book_name="Jeremiah",
        book_number=24,
        chapter_start=32,
        chapter_end=33,
        audio_url="https://example.com/ch32.mp3",
        audio_urls=[
            {"chapter": 32, "title": "Chapter 32", "url": "https://example.com/ch32.mp3"},
            {"chapter": 33, "title": "Chapter 33", "url": "https://example.com/ch33.mp3"},
        ],
        text="Bible reading text",
        doc_id="202026252",
    )
    week = WeeklyStudyData(
        week_date_range="September 7-13",
        year=2026,
        week_number=37,
        watchtower=wt,
        bible_reading=br,
    )
    return JWLibraryData(this_week=week, next_week=week)


@pytest.mark.asyncio
async def test_coordinator_update_success(hass: HomeAssistant) -> None:
    """Test successful data update."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test")
    mock_api = AsyncMock(spec=JWLibraryApiClient)
    mock_data = _sample_library_data()
    mock_api.async_get_library_data.return_value = mock_data

    coordinator = JWLibraryDataUpdateCoordinator(
        hass, mock_api, config_entry=entry
    )
    with patch("custom_components.jw_library.coordinator.async_track_point_in_time"):
        data = await coordinator._async_update_data()
        assert data == mock_data
        assert coordinator._retry_count == 0


@pytest.mark.asyncio
async def test_coordinator_schedule_next_midnight(hass: HomeAssistant) -> None:
    """Test scheduling update at next local midnight with 5-second buffer."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test")
    mock_api = AsyncMock(spec=JWLibraryApiClient)
    coordinator = JWLibraryDataUpdateCoordinator(
        hass, mock_api, config_entry=entry
    )

    mock_unsub = MagicMock()
    coordinator._unsub_midnight_timer = mock_unsub

    fixed_now = datetime(2026, 9, 10, 23, 15, 0, tzinfo=UTC)
    expected_midnight = dt_util.start_of_local_day(
        fixed_now + timedelta(days=1)
    ) + timedelta(seconds=5)

    with (
        patch(
            "custom_components.jw_library.coordinator.dt_util.now",
            return_value=fixed_now,
        ),
        patch(
            "custom_components.jw_library.coordinator.async_track_point_in_time"
        ) as mock_track,
    ):
        coordinator._schedule_next_midnight()

        mock_unsub.assert_called_once()
        mock_track.assert_called_once_with(
            hass,
            coordinator._async_scheduled_update,
            expected_midnight,
        )


@pytest.mark.asyncio
async def test_coordinator_retry_backoff_on_communication_error_no_cache(
    hass: HomeAssistant,
) -> None:
    """Test retry backoff on communication error without cached data."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test")
    mock_api = AsyncMock(spec=JWLibraryApiClient)
    mock_api.async_get_library_data.side_effect = (
        JWLibraryApiClientCommunicationError("Network unreachable")
    )

    coordinator = JWLibraryDataUpdateCoordinator(
        hass, mock_api, config_entry=entry
    )
    coordinator.data = None

    fixed_now = datetime(2026, 9, 10, 12, 0, 0, tzinfo=UTC)

    with (
        patch(
            "custom_components.jw_library.coordinator.dt_util.now",
            return_value=fixed_now,
        ),
        patch(
            "custom_components.jw_library.coordinator.async_track_point_in_time"
        ) as mock_track,
        pytest.raises(UpdateFailed),
    ):
        await coordinator._async_update_data()

    assert coordinator._retry_count == 1
    expected_retry_time = fixed_now + timedelta(minutes=2)
    mock_track.assert_called_once_with(
        hass,
        coordinator._async_scheduled_update,
        expected_retry_time,
    )


@pytest.mark.asyncio
async def test_coordinator_retry_backoff_exponential_cap(
    hass: HomeAssistant,
) -> None:
    """Test exponential backoff progression capped at 30 minutes."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test")
    mock_api = AsyncMock(spec=JWLibraryApiClient)
    mock_api.async_get_library_data.side_effect = (
        JWLibraryApiClientCommunicationError("Network down")
    )

    cached_data = _sample_library_data()
    coordinator = JWLibraryDataUpdateCoordinator(
        hass, mock_api, config_entry=entry
    )
    coordinator.data = cached_data

    fixed_now = datetime(2026, 9, 10, 12, 0, 0, tzinfo=UTC)
    expected_backoffs = [2, 4, 8, 16, 30, 30]

    with (
        patch(
            "custom_components.jw_library.coordinator.dt_util.now",
            return_value=fixed_now,
        ),
        patch(
            "custom_components.jw_library.coordinator.async_track_point_in_time"
        ) as mock_track,
    ):
        for idx, expected_minutes in enumerate(expected_backoffs, start=1):
            mock_track.reset_mock()
            data = await coordinator._async_update_data()
            assert data == cached_data
            assert coordinator._retry_count == idx
            expected_retry_time = fixed_now + timedelta(minutes=expected_minutes)
            mock_track.assert_called_once_with(
                hass,
                coordinator._async_scheduled_update,
                expected_retry_time,
            )


@pytest.mark.asyncio
async def test_coordinator_retry_preserves_cached_data(
    hass: HomeAssistant,
) -> None:
    """Test that communication failure preserves existing cached data."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test")
    mock_api = AsyncMock(spec=JWLibraryApiClient)
    cached_data = _sample_library_data()
    mock_api.async_get_library_data.return_value = cached_data

    coordinator = JWLibraryDataUpdateCoordinator(
        hass, mock_api, config_entry=entry
    )

    with patch(
        "custom_components.jw_library.coordinator.async_track_point_in_time"
    ):
        data = await coordinator._async_update_data()
        assert data == cached_data
        coordinator.data = data

        mock_api.async_get_library_data.side_effect = (
            JWLibraryApiClientCommunicationError("Temporary WOL outage")
        )
        data_after_error = await coordinator._async_update_data()

        assert data_after_error == cached_data
        assert coordinator._retry_count == 1


@pytest.mark.asyncio
async def test_coordinator_resets_retry_count_on_success(
    hass: HomeAssistant,
) -> None:
    """Test that retry count is reset to zero after successful update."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test")
    mock_api = AsyncMock(spec=JWLibraryApiClient)
    mock_data = _sample_library_data()
    mock_api.async_get_library_data.return_value = mock_data

    coordinator = JWLibraryDataUpdateCoordinator(
        hass, mock_api, config_entry=entry
    )
    coordinator._retry_count = 5

    with patch(
        "custom_components.jw_library.coordinator.async_track_point_in_time"
    ):
        await coordinator._async_update_data()
        assert coordinator._retry_count == 0


@pytest.mark.asyncio
async def test_coordinator_generic_api_error_raises_update_failed(
    hass: HomeAssistant,
) -> None:
    """Test non-communication API errors raise UpdateFailed directly."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test")
    mock_api = AsyncMock(spec=JWLibraryApiClient)
    mock_api.async_get_library_data.side_effect = JWLibraryApiClientError(
        "Unexpected error"
    )

    coordinator = JWLibraryDataUpdateCoordinator(
        hass, mock_api, config_entry=entry
    )
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_async_scheduled_update(
    hass: HomeAssistant,
) -> None:
    """Test _async_scheduled_update invokes async_refresh."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test")
    mock_api = AsyncMock(spec=JWLibraryApiClient)
    coordinator = JWLibraryDataUpdateCoordinator(
        hass, mock_api, config_entry=entry
    )
    coordinator.async_refresh = AsyncMock()

    await coordinator._async_scheduled_update(datetime.now(UTC))
    coordinator.async_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_coordinator_async_setup_midnight_schedule(
    hass: HomeAssistant,
) -> None:
    """Test async_setup_midnight_schedule invokes _schedule_next_midnight."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test")
    mock_api = AsyncMock(spec=JWLibraryApiClient)
    coordinator = JWLibraryDataUpdateCoordinator(
        hass, mock_api, config_entry=entry
    )

    with patch.object(coordinator, "_schedule_next_midnight") as mock_schedule:
        coordinator.async_setup_midnight_schedule()
        mock_schedule.assert_called_once()


@pytest.mark.asyncio
async def test_coordinator_async_shutdown(hass: HomeAssistant) -> None:
    """Test async_shutdown cancels midnight and retry timers."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test")
    mock_api = AsyncMock(spec=JWLibraryApiClient)
    coordinator = JWLibraryDataUpdateCoordinator(
        hass, mock_api, config_entry=entry
    )

    mock_midnight_unsub = MagicMock()
    mock_retry_unsub = MagicMock()
    coordinator._unsub_midnight_timer = mock_midnight_unsub
    coordinator._unsub_retry_timer = mock_retry_unsub

    await coordinator.async_shutdown()

    mock_midnight_unsub.assert_called_once()
    mock_retry_unsub.assert_called_once()
    assert coordinator._unsub_midnight_timer is None
    assert coordinator._unsub_retry_timer is None
