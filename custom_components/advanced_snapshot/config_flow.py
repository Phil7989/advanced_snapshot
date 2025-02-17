import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)

# Einfaches Schema für die Eingaben ohne feste Werte
DATA_SCHEMA = vol.Schema({
    vol.Required("snapshots_directory"): str,
    vol.Required("camera_entity"): cv.entity_id,
})

class AdvancedSnapshotConfigFlow(config_entries.ConfigFlow, domain="advanced_snapshot"):
    """Handle a simple config flow for Advanced Snapshot."""
    
    VERSION = 1

    def __init__(self):
        """Initialize the flow."""
        self.snapshots_directory = None
        self.camera_entity = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # Direkt die Eingabewerte speichern und den Flow abschließen
            self.snapshots_directory = user_input["snapshots_directory"]
            self.camera_entity = user_input["camera_entity"]

            # Speichern der Konfiguration ohne zusätzliche Validierung
            return self.async_create_entry(
                title="Advanced Snapshot",
                data={
                    "snapshots_directory": self.snapshots_directory,
                    "camera_entity": self.camera_entity,
                }
            )

        # Wenn keine Eingaben vorhanden sind, wird das Formular angezeigt
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA
        )
