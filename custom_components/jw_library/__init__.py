"""Custom integration to integrate JW Library with Home Assistant."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import JWLibraryApiClient
from .const import CONF_LANGUAGE, DEFAULT_LANGUAGE
from .coordinator import JWLibraryDataUpdateCoordinator
from .data import JWLibraryData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import JWLibraryConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JWLibraryConfigEntry,
) -> bool:
    """Set up JW Library from a config entry."""
    language = entry.options.get(
        CONF_LANGUAGE,
        entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
    )
    session = async_get_clientsession(hass)
    client = JWLibraryApiClient(session=session, language=language)

    coordinator = JWLibraryDataUpdateCoordinator(
        hass=hass,
        api_client=client,
        config_entry=entry,
    )
    await coordinator.async_config_entry_first_refresh()

    integration = None
    try:
        integration = async_get_loaded_integration(hass, entry.domain)
    except Exception:  # noqa: BLE001
        integration = None

    entry.runtime_data = JWLibraryData(
        client=client,
        coordinator=coordinator,
        integration=integration,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: JWLibraryConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.coordinator.async_shutdown()
    return unloaded
