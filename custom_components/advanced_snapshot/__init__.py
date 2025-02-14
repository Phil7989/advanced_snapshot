import logging
import os
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.camera import async_get_image
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

DOMAIN = "advanced_snapshot"

SERVICE_SCHEMA = vol.Schema({
    vol.Required("camera_entity_id"): cv.entity_id,
    vol.Required("file_path"): cv.string,
    vol.Optional("crop_x", default=0): vol.Coerce(int),
    vol.Optional("crop_y", default=0): vol.Coerce(int),
    vol.Optional("crop_width", default=0): vol.Coerce(int),
    vol.Optional("crop_height", default=0): vol.Coerce(int),
    vol.Optional("add_bar", default=False): cv.boolean,
    vol.Optional("custom_text_left", default=""): cv.string,
    vol.Optional("custom_text_right", default=""): cv.string,
})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Advanced Snapshot integration."""

    async def handle_take_snapshot(call: ServiceCall):
        """Handle the service call to take a snapshot."""
        camera_entity_id = call.data["camera_entity_id"]
        file_path = call.data["file_path"]
        crop_x = call.data.get("crop_x", 0)
        crop_y = call.data.get("crop_y", 0)
        crop_width = call.data.get("crop_width", 0)
        crop_height = call.data.get("crop_height", 0)
        add_bar = call.data.get("add_bar", False)
        custom_text = call.data.get("custom_text", "")

        _LOGGER.info("Snapshot von %s wird aufgenommen und unter %s gespeichert", camera_entity_id, file_path)

        # Kamera-Bild abrufen
        try:
            image = await async_get_image(hass, camera_entity_id)
            if image is None or not hasattr(image, "content"):
                _LOGGER.error("Fehler: Bild konnte nicht abgerufen werden")
                return

            image_bytes = image.content

        except Exception as e:
            _LOGGER.error("Fehler beim Abrufen des Bildes: %s", e)
            return

        try:
            img = Image.open(BytesIO(image_bytes))

            # Falls Crop-Werte gesetzt sind, Bild zuschneiden
            if crop_width > 0 and crop_height > 0:
                img = img.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))

            # Falls Balken aktiviert ist, Text hinzufügen
            if add_bar:
                img = add_text_bar(img, custom_text_left, custom_text_right)

            # Sicherstellen, dass der Speicherpfad existiert
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Bild speichern
            img.save(file_path)
            _LOGGER.info("Snapshot erfolgreich gespeichert: %s", file_path)

        except Exception as e:
            _LOGGER.error("Fehler beim Verarbeiten oder Speichern des Bildes: %s", e)

    # Dienst registrieren
    hass.services.async_register(DOMAIN, "take_snapshot", handle_take_snapshot, schema=SERVICE_SCHEMA)

    _LOGGER.info("AdvancedSnapshot Integration erfolgreich eingerichtet")
    return True

def add_text_bar(img: Image.Image, custom_text_left: str, custom_text_right: str) -> Image.Image:
    """Fügt einen weißen Balken mit Zeitstempel & Namen unter das Bild hinzu."""
    width, height = img.size
    bar_height = 50  # Höhe des Balkens

    # Neues Bild mit Platz für den Balken
    new_img = Image.new("RGB", (width, height + bar_height), "white")
    new_img.paste(img, (0, 0))

    draw = ImageDraw.Draw(new_img)

    # Standard-Schriftart verwenden (falls keine TTF verfügbar ist)
    font = ImageFont.load_default()

    # Text für den Balken
    text = f"{custom_text_right} | {custom_text_left}" if custom_text else timestamp

    # Text mittig positionieren
    text_x = 10
    text_y = height + (bar_height // 4)

    draw.text((text_x, text_y), text, fill="black", font=font)

    return new_img
