from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, CONF_FONT_FOLDER, CONF_BACKUP_FOLDER, CONF_SNAPSHOT_FOLDER

class AdvancedSnapshotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Advanced Snapshot."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        # Prüfen, ob bereits ein ConfigEntry für diese Integration existiert
        if self._is_entry_existing():
            # Fehlermeldung ausgeben, aber kein Formular öffnen
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            return self.async_create_entry(title="Advanced Snapshot", data=user_input)

        return self.async_show_form(step_id="user", data_schema=self._get_schema(), errors=errors)

    def _is_entry_existing(self):
        """Prüfen, ob ein ConfigEntry für diese Integration existiert."""
        existing_entries = self.hass.config_entries.async_entries(DOMAIN)
        return len(existing_entries) > 0

    def _get_schema(self):
        """Gibt das Schema für das Formular zurück."""
        return vol.Schema({
            vol.Required(CONF_FONT_FOLDER, default="/config/fonts"): str,
            vol.Required(CONF_BACKUP_FOLDER, default="/config/backups"): str,
            vol.Required(CONF_SNAPSHOT_FOLDER, default="/config/snapshots"): str,
        })

    @staticmethod
    @config_entries.HANDLERS.register(DOMAIN)
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return AdvancedSnapshotOptionsFlowHandler(config_entry)

class AdvancedSnapshotOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Advanced Snapshot."""

    async def async_step_init(self, user_input=None):
        """Manage the options for the integration."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Hier auf config_entry direkt zugreifen
        schema = vol.Schema({
            vol.Required(CONF_FONT_FOLDER, default=self.config_entry.options.get(CONF_FONT_FOLDER, "/config/fonts")): str,
            vol.Required(CONF_BACKUP_FOLDER, default=self.config_entry.options.get(CONF_BACKUP_FOLDER, "/config/backups")): str,
            vol.Required(CONF_SNAPSHOT_FOLDER, default=self.config_entry.options.get(CONF_SNAPSHOT_FOLDER, "/config/snapshots")): str,
        })

        return self.async_show_form(step_id="init", data_schema=schema)
