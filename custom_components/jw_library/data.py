"""Custom types for jw_library."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import JWLibraryApiClient
    from .coordinator import JWLibraryDataUpdateCoordinator


type JWLibraryConfigEntry = ConfigEntry[JWLibraryData]


@dataclass
class JWLibraryData:
    """Data for the JW Library integration."""

    client: JWLibraryApiClient
    coordinator: JWLibraryDataUpdateCoordinator
    integration: Integration | None = None
