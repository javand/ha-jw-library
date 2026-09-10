"""Unit tests for integration setup and unload lifecycle."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jw_library import (
    async_reload_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.jw_library.const import CONF_LANGUAGE, DOMAIN
from tests.test_coordinator import _sample_library_data


@pytest.mark.asyncio
async def test_setup_unload_entry(hass: HomeAssistant) -> None:
    """Test setting up and unloading the integration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="test_jw_library",
        data={CONF_LANGUAGE: "english"},
    )
    entry.add_to_hass(hass)
    entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)

    mock_data = _sample_library_data()

    with (
        patch(
            "custom_components.jw_library.api.JWLibraryApiClient.async_get_library_data",
            AsyncMock(return_value=mock_data),
        ),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
            AsyncMock(return_value=True),
        ),
    ):
        assert await async_setup_entry(hass, entry) is True
        assert entry.runtime_data is not None
        assert entry.runtime_data.coordinator.data == mock_data

        with patch(
            "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
            AsyncMock(return_value=True),
        ):
            assert await async_unload_entry(hass, entry) is True


@pytest.mark.asyncio
async def test_reload_entry(hass: HomeAssistant) -> None:
    """Test reloading the integration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="test_jw_library",
        data={CONF_LANGUAGE: "english"},
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.jw_library.async_unload_entry",
            AsyncMock(return_value=True),
        ) as mock_unload,
        patch(
            "custom_components.jw_library.async_setup_entry",
            AsyncMock(return_value=True),
        ) as mock_setup,
    ):
        await async_reload_entry(hass, entry)
        mock_unload.assert_awaited_once_with(hass, entry)
        mock_setup.assert_awaited_once_with(hass, entry)
