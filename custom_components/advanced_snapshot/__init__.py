import os
import logging
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import aiofiles
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.components.camera import async_get_image
from functools import partial
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA = vol.Schema({
    vol.Required("camera_entity_id"): cv.entity_id,
    vol.Required("file_path"): cv.string,
    vol.Optional("file_path_backup"): cv.string,
    vol.Optional("crop", default=None): vol.Any(None, [vol.Coerce(int)]),
    vol.Optional("crop_aspect_ratio", default=None): vol.Any(None, vol.Match(r"^\d+:\d+$")),
    vol.Optional("add_bar", default=False): cv.boolean,
    vol.Optional("custom_text_left", default=""): cv.string,
    vol.Optional("custom_text_middle", default=""): cv.string,
    vol.Optional("custom_text_right", default=""): cv.string,
    vol.Optional("setting_font_path", default="/config/custom_components/advanced_snapshot/fonts/Arial.ttf"): cv.string,
    vol.Optional("setting_font_size", default="auto"): vol.Any(vol.Coerce(int), vol.In(["auto"])),
    vol.Optional("setting_font_color", default="black"): cv.string,
    vol.Optional("setting_bar_height", default="40"): vol.Any(vol.Coerce(int), vol.Match(r"^\d+%$")),
    vol.Optional("setting_bar_color", default="white"): cv.string,
    vol.Optional("setting_bar_position", default="bottom"): cv.string
})

async def async_setup(hass: HomeAssistant, config: dict):
    _LOGGER.info("Registering the take_snapshot service.")
    hass.services.async_register(
        DOMAIN, "take_snapshot", partial(handle_take_snapshot, hass),
        schema=SERVICE_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info(f"Loading Advanced Snapshot configuration: {entry.data}")
    hass.data[DOMAIN] = entry.data
    hass.services.async_register(
        DOMAIN, "take_snapshot", partial(handle_take_snapshot, hass),
        schema=SERVICE_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Unloading Advanced Snapshot integration.")
    hass.services.async_remove(DOMAIN, "take_snapshot")
    if DOMAIN in hass.data:
        del hass.data[DOMAIN]
    return True

async def handle_take_snapshot(hass: HomeAssistant, call: ServiceCall) -> ServiceResponse:
    _LOGGER.info("Received snapshot request.")
    try:
        camera_entity_id = call.data["camera_entity_id"]
        file_path = call.data["file_path"]
        file_path_backup = call.data.get("file_path_backup")
        setting_font_path = call.data.get("setting_font_path")

        snapshot_folder = hass.data.get(DOMAIN, {}).get("snapshot_folder")
        backup_folder = hass.data.get(DOMAIN, {}).get("backup_folder")
        font_folder = hass.data.get(DOMAIN, {}).get("font_folder")

        if not os.path.isabs(file_path):
            file_path = os.path.join(snapshot_folder, file_path)

        if file_path_backup and not os.path.isabs(file_path_backup):
            file_path_backup = os.path.join(backup_folder, file_path_backup)

        if not os.path.isabs(setting_font_path):
            setting_font_path = os.path.join(font_folder, setting_font_path)
        if not os.path.splitext(setting_font_path)[1]:  
            setting_font_path += ".ttf"
        crop = call.data.get("crop")
        crop_aspect_ratio = call.data.get("crop_aspect_ratio")
        add_bar = call.data.get("add_bar", False)
        custom_text_left = call.data.get("custom_text_left", "")
        custom_text_middle = call.data.get("custom_text_middle", "")
        custom_text_right = call.data.get("custom_text_right", "")
        setting_font_size = call.data.get("setting_font_size")
        setting_bar_height = call.data.get("setting_bar_height")
        setting_bar_color = call.data.get("setting_bar_color", "white")
        setting_bar_position = call.data.get("setting_bar_position", "bottom")

        event_data = {
            "success": False,
            "file_path": file_path,
            "backup_path": file_path_backup,
            "original_resolution": None,
            "final_resolution": None,
            "error": None
        }

        image = await async_get_image(hass, camera_entity_id)
        if image is None or not hasattr(image, "content"):
            _LOGGER.error("Failed to retrieve image from camera.")
            event_data["error"] = "Image could not be retrieved"
            return event_data

        img = Image.open(BytesIO(image.content))
        event_data["original_resolution"] = [img.width, img.height]
        
        if crop:
            if len(crop) < 3:
                _LOGGER.error("Invalid crop values: crop must have at least [x, y, width]")
                event_data["error"] = "Invalid crop values"
                return event_data

            x, y, w = crop[:3]
            h = crop[3] if len(crop) == 4 else None

            if crop_aspect_ratio:
                try:
                    aspect_w, aspect_h = map(int, crop_aspect_ratio.split(":"))
                    h = int(w * (aspect_h / aspect_w))
                    _LOGGER.info(f"Using aspect ratio {crop_aspect_ratio}, calculated height: {h}")
                except ValueError:
                    _LOGGER.error(f"Invalid aspect ratio format: {crop_aspect_ratio}")
                    event_data["error"] = "Invalid aspect ratio format"
                    return event_data

            if h is None:
                _LOGGER.error("Height (h) is missing and no aspect ratio provided.")
                event_data["error"] = "Height (h) is missing and no aspect ratio provided."
                return event_data

            if x < 0 or y < 0 or w <= 0 or h <= 0:
                _LOGGER.error(f"Invalid crop dimensions: {x, y, w, h}")
                event_data["error"] = "Invalid crop dimensions"
                return event_data

            if (x + w) > img.width or (y + h) > img.height:
                _LOGGER.error(f"Invalid crop area: ({x}, {y}, {w}, {h}) exceeds image size")
                event_data["error"] = "Invalid crop area"
                return event_data
            
            img = img.crop((x, y, x + w, y + h))

        if add_bar:
            _LOGGER.debug("Adding text bar to image.")
            img = add_text_bar(
                img, custom_text_left, custom_text_middle, custom_text_right,
                setting_font_path, setting_font_size, "black",
                setting_bar_height, setting_bar_color, setting_bar_position, event_data
            )

        event_data["final_resolution"] = [img.width, img.height]

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        await async_save_image(img, file_path)
        _LOGGER.info(f"Snapshot saved at {file_path}")

        if file_path_backup:
            try:
                os.makedirs(os.path.dirname(file_path_backup), exist_ok=True)
                await async_save_image(img, file_path_backup)
                _LOGGER.info(f"Backup snapshot saved at {file_path_backup}")
                event_data["backup_path"] = file_path_backup
            except Exception as e:
                _LOGGER.error(f"Backup failed: {str(e)}")
                event_data["error"] = f"Backup failed: {str(e)}"
                event_data["success"] = False  

        event_data["success"] = True

    except Exception as e:
        _LOGGER.exception(f"Error while taking snapshot: {str(e)}")
        event_data["error"] = str(e)

    return event_data

def add_text_bar(img: Image.Image, custom_text_left: str, custom_text_middle: str,
                 custom_text_right: str, setting_font_path: str, setting_font_size,
                 setting_font_color: str, setting_bar_height,
                 setting_bar_color: str, setting_bar_position: str, event_data: dict) -> Image.Image:
    width, height = img.size

    if isinstance(setting_bar_height, str) and setting_bar_height.endswith('%'):
        try:
            percentage = float(setting_bar_height.strip('%')) / 100.0
            bar_height = int(height * percentage)
        except ValueError:
            _LOGGER.warning(f"Invalid percentage value for setting_bar_height: {setting_bar_height}. Using default 40px.")
            event_data["error"] = f"Invalid percentage value: {setting_bar_height}. Using default 40px."
            bar_height = 40
    else:
        try:
            bar_height = int(setting_bar_height)
        except ValueError:
            _LOGGER.warning(f"Invalid pixel value for setting_bar_height: {setting_bar_height}. Using default 40px.")
            event_data["error"] = f"Invalid pixel value: {setting_bar_height}. Using default 40px."
            bar_height = 40 

    if setting_font_size == "auto":
        setting_font_size = max(10, int(bar_height * 0.5))

    if setting_bar_position == "top":
        new_img = Image.new("RGB", (width, height + bar_height), setting_bar_color)
        new_img.paste(img, (0, bar_height))
        text_y = (bar_height - setting_font_size) // 2
    else:
        new_img = Image.new("RGB", (width, height + bar_height), setting_bar_color)
        new_img.paste(img, (0, 0))
        text_y = height + (bar_height - setting_font_size) // 2

    draw = ImageDraw.Draw(new_img)
    try:
        font = ImageFont.truetype(setting_font_path, setting_font_size)
    except IOError:
        _LOGGER.warning(f"Font file not found: {setting_font_path}, using default font.")
        event_data["error"] = f"Font file not found: {setting_font_path}, using default font."
        font = ImageFont.load_default()

    draw.text((10, text_y), custom_text_left, fill=setting_font_color, font=font)
    draw.text(((width - draw.textlength(custom_text_middle, font=font)) // 2, text_y),
              custom_text_middle, fill=setting_font_color, font=font)
    draw.text((width - draw.textlength(custom_text_right, font=font) - 10, text_y),
              custom_text_right, fill=setting_font_color, font=font)

    return new_img


async def async_save_image(img: Image.Image, file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    format_map = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG"}
    image_format = format_map.get(ext, "JPEG")

    async with aiofiles.open(file_path, "wb") as f:
        buffer = BytesIO()
        img.save(buffer, format=image_format)
        buffer.seek(0)
        await f.write(buffer.getvalue())

    _LOGGER.info(f"Snapshot saved: {file_path} ({image_format})")