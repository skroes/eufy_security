import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.components.select import SelectEntity
from homeassistant.const import (
    ENERGY_KILO_WATT_HOUR,
    PERCENTAGE,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_SIGNAL_STRENGTH,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from .const import COORDINATOR, DOMAIN, Device
from. const import get_child_value
from .entity import EufySecurityEntity
from .coordinator import EufySecurityDataUpdateCoordinator

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_devices):
    coordinator: EufySecurityDataUpdateCoordinator = hass.data[DOMAIN][COORDINATOR]

    INSTRUMENTS = [
        ("night_vision", "Night Vision", "nightvision", EntityCategory.CONFIG),
        ("power_working_mode", "Power Working Mode", "powerWorkingMode", EntityCategory.CONFIG),
        ("video_streaming_quality", "Video Streaming Quality", "videoStreamingQuality", EntityCategory.CONFIG),
        ("video_recording_quality", "Video Recording Quality", "videoRecordingQuality", EntityCategory.CONFIG),
        ("motion_detection_type", "Motion Detection Type", "motionDetectionType", EntityCategory.CONFIG),
        ("rotation_speed", "Rotation Speed", "rotationSpeed", EntityCategory.CONFIG),
    ]

    entities = []
    for device in coordinator.devices.values():
        instruments = INSTRUMENTS
        for id, description, key, entity_category in instruments:
            if not get_child_value(device.state, key) is None:
                entities.append(EufySelectEntity(coordinator, config_entry, device, id, description, key, entity_category))

    async_add_devices(entities, True)


class EufySelectEntity(EufySecurityEntity, SelectEntity):
    def __init__(self, coordinator: EufySecurityDataUpdateCoordinator, config_entry: ConfigEntry, device: Device, id: str, description: str, key: str, entity_category: str):
        EufySecurityEntity.__init__(self, coordinator, config_entry, device)
        SelectEntity.__init__(self)
        self._id = id
        self.description = description
        self.key = key
        self.states = get_child_value(self.device.properties_metadata, self.key)
        _LOGGER.debug(f"{DOMAIN} - {self.device.name} - {self.id} - select init - {self.states}")
        self.values_to_states = self.states.get("states", {})
        self.states_to_values = {v: k for k, v in self.values_to_states.items()}
        self._attr_options: list[str] = list(self.values_to_states.values())
        self._attr_entity_category = entity_category

        _LOGGER.debug(f"{DOMAIN} - {self.device.name} - {self.id} - select init - {self.values_to_states} - {self.states_to_values}")

    async def async_select_option(self, option: str):
        await self.coordinator.async_set_property(self.device.serial_number, self.key, self.states_to_values[option])

    @property
    def current_option(self) -> str:
        return self.values_to_states[str(get_child_value(self.device.state, self.key))]

    @property
    def name(self):
        return f"{self.device.name} {self.description}"

    @property
    def id(self):
        return f"{DOMAIN}_{self.device.serial_number}_{self._id}_select"

    @property
    def unique_id(self):
        return self.id