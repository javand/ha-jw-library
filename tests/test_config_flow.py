"""Unit tests for JW Library config flow and options flow."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jw_library.config_flow import (
    JWLibraryConfigFlow,
    JWLibraryOptionsFlowHandler,
)
from custom_components.jw_library.const import (
    CONF_LANGUAGE,
    DEFAULT_LANGUAGE,
    DOMAIN,
    NAME,
    SUPPORTED_LANGUAGES,
)


@pytest.mark.asyncio
async def test_config_flow_user_step_form() -> None:
    """Test showing the user configuration form with default language."""
    flow = JWLibraryConfigFlow()
    flow.hass = MagicMock()

    result = await flow.async_step_user()
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["data_schema"] is not None

    schema = result["data_schema"].schema
    lang_key = next(k for k in schema if k == CONF_LANGUAGE)
    assert lang_key.default() == DEFAULT_LANGUAGE
    assert schema[lang_key].container == SUPPORTED_LANGUAGES


@pytest.mark.asyncio
async def test_config_flow_user_step_create_entry() -> None:
    """Test creating an entry when user input is valid."""
    flow = JWLibraryConfigFlow()
    flow.hass = MagicMock()
    flow.context = {}
    flow.hass.config_entries.flow.async_progress_by_handler.return_value = []
    flow.hass.config_entries.async_entry_for_domain_unique_id.return_value = None

    result = await flow.async_step_user(user_input={CONF_LANGUAGE: "spanish"})
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"] == {CONF_LANGUAGE: "spanish"}
    assert flow.unique_id == DOMAIN


@pytest.mark.asyncio
async def test_config_flow_user_step_already_configured() -> None:
    """Test aborting the flow if already configured."""
    flow = JWLibraryConfigFlow()
    flow.hass = MagicMock()
    flow.context = {}
    flow.hass.config_entries.flow.async_progress_by_handler.return_value = []
    existing_entry = MagicMock()
    flow.hass.config_entries.async_entry_for_domain_unique_id.return_value = (
        existing_entry
    )

    with pytest.raises(data_entry_flow.AbortFlow) as exc_info:
        await flow.async_step_user(user_input={CONF_LANGUAGE: "english"})
    assert exc_info.value.reason == "already_configured"


def test_config_flow_async_get_options_flow() -> None:
    """Test obtaining the options flow handler from config flow."""
    mock_entry = MagicMock(spec=config_entries.ConfigEntry)
    options_flow = JWLibraryConfigFlow.async_get_options_flow(mock_entry)
    assert isinstance(options_flow, JWLibraryOptionsFlowHandler)


@pytest.mark.asyncio
async def test_options_flow_init_step_form_default_data(hass: HomeAssistant) -> None:
    """Test options flow shows form with default language from entry data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="test_jw_library",
        data={CONF_LANGUAGE: "spanish"},
        options={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["data_schema"] is not None

    schema = result["data_schema"].schema
    lang_key = next(k for k in schema if k == CONF_LANGUAGE)
    assert lang_key.default() == "spanish"
    assert schema[lang_key].container == SUPPORTED_LANGUAGES


@pytest.mark.asyncio
async def test_options_flow_init_step_form_default_options(
    hass: HomeAssistant,
) -> None:
    """Test options flow prioritizing options over data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="test_jw_library",
        data={CONF_LANGUAGE: "english"},
        options={CONF_LANGUAGE: "french"},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    schema = result["data_schema"].schema
    lang_key = next(k for k in schema if k == CONF_LANGUAGE)
    assert lang_key.default() == "french"


@pytest.mark.asyncio
async def test_options_flow_init_step_create_entry(hass: HomeAssistant) -> None:
    """Test options flow updates options on user submit and triggers reload."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="test_jw_library",
        data={CONF_LANGUAGE: "english"},
        options={CONF_LANGUAGE: "english"},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_reload", AsyncMock()
    ) as mock_reload:
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_LANGUAGE: "portuguese"},
        )
        assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result2["data"] == {CONF_LANGUAGE: "portuguese"}
        assert entry.options == {CONF_LANGUAGE: "portuguese"}
        mock_reload.assert_awaited_once_with(entry.entry_id)


def test_translations_en_structure() -> None:
    """Test translations en.json schema."""
    en_path = (
        Path(__file__).parent.parent
        / "custom_components"
        / "jw_library"
        / "translations"
        / "en.json"
    )
    with en_path.open(encoding="utf-8") as f:
        data = json.load(f)

    assert "config" in data
    assert "step" in data["config"]
    assert "user" in data["config"]["step"]
    user_step = data["config"]["step"]["user"]
    assert user_step["title"] == "JW Library"
    assert "description" in user_step
    assert user_step["data"]["language"] == "Language"

    assert "abort" in data["config"]
    assert "already_configured" in data["config"]["abort"]

    assert "options" in data
    assert "step" in data["options"]
    assert "init" in data["options"]["step"]
    init_step = data["options"]["step"]["init"]
    assert init_step["title"] == "JW Library Options"
    assert init_step["data"]["language"] == "Language"
