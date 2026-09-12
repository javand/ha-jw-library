"""Config flow for jw_library."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_LANGUAGE,
    DEFAULT_LANGUAGE,
    DOMAIN,
    NAME,
    SUPPORTED_LANGUAGES,
)

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult


class JWLibraryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for JW Library."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=NAME,
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(
                    SUPPORTED_LANGUAGES
                )
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return JWLibraryOptionsFlowHandler(config_entry)


class JWLibraryOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for JW Library."""

    def __init__(self, config_entry: config_entries.ConfigEntry | None = None) -> None:
        """Initialize options flow."""
        self._custom_config_entry = config_entry

    @property
    def config_entry(self) -> config_entries.ConfigEntry:
        """Return config entry."""
        if self._custom_config_entry is not None:
            return self._custom_config_entry
        return super().config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_lang = self.config_entry.options.get(
            CONF_LANGUAGE,
            self.config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
        )
        if current_lang not in SUPPORTED_LANGUAGES:
            current_lang = DEFAULT_LANGUAGE

        schema = vol.Schema(
            {
                vol.Required(CONF_LANGUAGE, default=current_lang): vol.In(
                    SUPPORTED_LANGUAGES
                )
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
