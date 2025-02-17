from homeassistant import config_entries

class AdvancedSnapshotConfigFlow(config_entries.ConfigFlow, domain="advanced_snapshot"):
    """Handle a simple config flow for Advanced Snapshot."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Just complete the flow without any user input or configuration."""
        return self.async_create_entry(
            title="Advanced Snapshot",
            data={},
        )
