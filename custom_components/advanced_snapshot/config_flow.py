import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.config_entries import OptionsFlow  

from .const import DOMAIN

class AdvancedSnapshotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Advanced Snapshot."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if self._is_entry_existing():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            return self.async_create_entry(title=DOMAIN, data=user_input)

        return self.async_show_form(step_id="user", data_schema=self._get_schema(), 
    description_placeholders={}, errors=errors)

    def _is_entry_existing(self):
        existing_entries = self.hass.config_entries.async_entries(DOMAIN)
        return len(existing_entries) > 0

    def _get_schema(self):
        return vol.Schema({
            vol.Required("font_folder", default="/config/custom_components/advanced_snapshot/fonts"): str,
            vol.Required("snapshot_folder", default="/config/www/backupsnapshots/"): str,
            vol.Required("backup_folder", default="/config/www/snapshots/"): str,
        })

    @staticmethod
    @config_entries.HANDLERS.register(DOMAIN)
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return AdvancedSnapshotOptionsFlowHandler(config_entry)
        
class AdvancedSnapshotOptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry):
        """Initialize options flow."""
        self.entry_id = config_entry.entry_id  

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        config_entry = self.hass.config_entries.async_get_entry(self.entry_id)  

        if not config_entry:
            return self.async_abort(reason="config_entry_not_found")

        if user_input is not None:
            self.hass.config_entries.async_update_entry(config_entry, data={**config_entry.data, **user_input})
            return self.async_create_entry(title=DOMAIN, data={})
        
        data = self.config_entry.data
        
        schema = vol.Schema({
            vol.Required("font_folder", default=data.get("font_folder", "/config/custom_components/advanced_snapshot/fonts")): str,
            vol.Required("snapshot_folder", default=data.get("snapshot_folder", "/config/www/backupsnapshots/")): str,
            vol.Required("backup_folder", default=data.get("backup_folder", "/config/www/snapshots/")): str,
        })
        
        return self.async_show_form(step_id="init", data_schema=schema)