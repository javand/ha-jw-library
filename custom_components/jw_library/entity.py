"""Base entity for the JW Library integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, NAME
from .coordinator import JWLibraryDataUpdateCoordinator


class JWLibraryEntity(CoordinatorEntity[JWLibraryDataUpdateCoordinator]):
    """Defines a base JW Library entity."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: JWLibraryDataUpdateCoordinator,
        unique_id: str,
    ) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._attr_unique_id = unique_id

        entry_id = getattr(getattr(coordinator, "config_entry", None), "entry_id", None)
        domain = getattr(getattr(coordinator, "config_entry", None), "domain", DOMAIN)
        if entry_id:
            self._attr_device_info = DeviceInfo(
                identifiers={(domain, entry_id)},
                name=NAME,
                manufacturer="Watchtower",
                model="Weekly Study & Audio",
            )
