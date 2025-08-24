from __future__ import annotations

from .logger import _LOGGER
from typing import Any, Final

from homeassistant.components.light import (
    ENTITY_ID_FORMAT,
    LightEntity,
    LightEntityDescription,
    ColorMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_LIGHT_LED, ATTR_LIGHT_LED_NAME, ATTR_STATE
from .entity import MiWifiEntity
from .exceptions import LuciError
from .updater import LuciUpdater, async_get_updater

PARALLEL_UPDATES = 0

ICONS: Final = {
    f"{ATTR_LIGHT_LED}_{STATE_ON}": "mdi:led-on",
    f"{ATTR_LIGHT_LED}_{STATE_OFF}": "mdi:led-off",
}

MIWIFI_LIGHTS: tuple[LightEntityDescription, ...] = (
    LightEntityDescription(
        key=ATTR_LIGHT_LED,
        name=ATTR_LIGHT_LED_NAME,
        icon=ICONS[f"{ATTR_LIGHT_LED}_{STATE_ON}"],
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=True,
    ),
)




async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MiWifi light entry."""

    updater: LuciUpdater = async_get_updater(hass, config_entry.entry_id)

    async_add_entities([
        MiWifiLight(
            f"{config_entry.entry_id}-{ATTR_LIGHT_LED}",
            MIWIFI_LIGHTS[0],
            updater,
        )
    ])


class MiWifiLight(MiWifiEntity, LightEntity):
    """MiWifi light entity for controlling router LED."""

    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        unique_id: str,
        description: LightEntityDescription,
        updater: LuciUpdater,
    ) -> None:
        super().__init__(unique_id, description, updater, ENTITY_ID_FORMAT)
        self._attr_is_on = updater.data.get(description.key, False)
        self._attr_available = updater.data.get(ATTR_STATE, True)

    @property
    def icon(self) -> str | None:
        state = STATE_ON if self._attr_is_on else STATE_OFF
        return ICONS.get(f"{self.entity_description.key}_{state}")

    def _handle_coordinator_update(self) -> None:
        """Update state on data refresh."""
        is_on = self._updater.data.get(self.entity_description.key, False)
        is_available = self._updater.data.get(ATTR_STATE, True)

        if self._attr_is_on != is_on or self._attr_available != is_available:
            self._attr_is_on = is_on
            self._attr_available = is_available
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._led_action(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._led_action(False)

    async def _led_action(self, turn_on: bool) -> None:
        try:
            await self._updater.luci.led(1 if turn_on else 0)
        except LuciError:
            return

        self._attr_is_on = turn_on
        self._updater.data[self.entity_description.key] = turn_on
        self.async_write_ha_state()
