"""DataUpdateCoordinator for jw_library."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .api import (
    JWLibraryApiClient,
    JWLibraryApiClientCommunicationError,
    JWLibraryApiClientError,
    JWLibraryData,
)
from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class JWLibraryDataUpdateCoordinator(DataUpdateCoordinator[JWLibraryData]):
    """Class to manage fetching JW Library weekly study data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: JWLibraryApiClient,
        config_entry: Any | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            **kwargs,
        )
        self.api_client = api_client
        self._unsub_midnight_timer: Callable[[], None] | None = None
        self._unsub_retry_timer: Callable[[], None] | None = None
        self._retry_count = 0

    async def _async_update_data(self) -> JWLibraryData:
        """Fetch weekly data from WOL and JW CDN."""
        now = dt_util.now()
        today_date = now.date()

        try:
            data = await self.api_client.async_get_library_data(base_date=today_date)
        except JWLibraryApiClientCommunicationError as err:
            self._retry_count += 1
            backoff_minutes = min(2**self._retry_count, 30)
            LOGGER.warning(
                "Error fetching JW Library data (%s). Retrying in %d minutes.",
                err,
                backoff_minutes,
            )
            retry_time = dt_util.now() + timedelta(minutes=backoff_minutes)
            if self._unsub_retry_timer is not None:
                self._unsub_retry_timer()
                self._unsub_retry_timer = None
            self._unsub_retry_timer = async_track_point_in_time(
                self.hass, self._async_scheduled_update, retry_time
            )
            if self.data is not None:
                return self.data
            raise UpdateFailed(err) from err
        except JWLibraryApiClientError as err:
            raise UpdateFailed(err) from err
        else:
            self._retry_count = 0
            if self._unsub_retry_timer is not None:
                self._unsub_retry_timer()
                self._unsub_retry_timer = None
            self._schedule_next_midnight()
            return data

    def _schedule_next_midnight(self) -> None:
        """Schedule next update at local midnight for week rollover."""
        if self._unsub_midnight_timer is not None:
            self._unsub_midnight_timer()
            self._unsub_midnight_timer = None

        now = dt_util.now()
        tomorrow_start = dt_util.start_of_local_day(now + timedelta(days=1))
        next_midnight = tomorrow_start + timedelta(seconds=5)

        self._unsub_midnight_timer = async_track_point_in_time(
            self.hass, self._async_scheduled_update, next_midnight
        )

    async def _async_scheduled_update(self, _now: datetime | None = None) -> None:
        """Handle scheduled update timer."""
        await self.async_refresh()

    def async_setup_midnight_schedule(self) -> None:
        """Expose midnight schedule setup."""
        self._schedule_next_midnight()

    async def async_shutdown(self) -> None:
        """Cancel any scheduled updates."""
        if self._unsub_midnight_timer is not None:
            self._unsub_midnight_timer()
            self._unsub_midnight_timer = None
        if self._unsub_retry_timer is not None:
            self._unsub_retry_timer()
            self._unsub_retry_timer = None
        await super().async_shutdown()
