import os
import logging
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import aiofiles
import asyncio
import datetime
import math
import codecs
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.components.camera import async_get_image
from homeassistant.components.camera import async_get_stream_source
from homeassistant.components.ffmpeg import get_ffmpeg_manager
import ffmpeg  
import subprocess
from functools import partial
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from .const import DOMAIN

    

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA = vol.Schema({
    vol.Required("camera_entity_id"): cv.entity_id,
    vol.Required("file_path"): cv.string,
    vol.Optional("file_path_backup"): cv.string,
    vol.Optional("rotate_angle", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=360)),
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

SERVICE_SCHEMA_RECORD_VIDEO = vol.Schema({
    vol.Required("camera_entity_id"): cv.entity_id,
    vol.Required("file_path"): cv.string,
    vol.Optional("file_path_backup"): cv.string,
    vol.Optional("duration", default=40): vol.All(vol.Coerce(int), vol.Range(min=1, max=40)),
    vol.Optional("rotate_angle", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=360)),
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

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

async def async_setup(hass: HomeAssistant, config: dict):
    _LOGGER.info("Registering the take_snapshot service.")
    hass.services.async_register(
        DOMAIN, "take_snapshot", partial(handle_take_snapshot, hass),
        schema=SERVICE_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )
    hass.services.async_register(
        DOMAIN, "record_video", partial(handle_record_video, hass),
        schema=SERVICE_SCHEMA_RECORD_VIDEO, supports_response=SupportsResponse.OPTIONAL
    )
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info(f"Loading Advanced Snapshot configuration: {entry.data}")
    hass.data[DOMAIN] = entry.data
    hass.services.async_register(
        DOMAIN, "take_snapshot", partial(handle_take_snapshot, hass),
        schema=SERVICE_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )
    hass.services.async_register(
        DOMAIN, "record_video", partial(handle_record_video, hass),
        schema=SERVICE_SCHEMA_RECORD_VIDEO, supports_response=SupportsResponse.OPTIONAL
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Unloading Advanced Snapshot integration.")
    hass.services.async_remove(DOMAIN, "take_snapshot")
    hass.services.async_remove(DOMAIN, "handle_record_video")
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
        rotate_angle = call.data.get("rotate_angle")
        crop = call.data.get("crop")
        crop_aspect_ratio = call.data.get("crop_aspect_ratio")
        add_bar = call.data.get("add_bar", False)
        custom_text_left = call.data.get("custom_text_left", "")
        custom_text_middle = call.data.get("custom_text_middle", "")
        custom_text_right = call.data.get("custom_text_right", "")
        setting_font_size = call.data.get("setting_font_size")
        setting_font_color = call.data.get("setting_font_color", "black")
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
        
        if rotate_angle:
            img = img.rotate(rotate_angle, expand=True)
            _LOGGER.info(f"Rotated image by {rotate_angle} degrees")
            
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
                setting_font_path, setting_font_size, setting_font_color,
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
    
async def handle_record_video(hass: HomeAssistant, call: ServiceCall) -> ServiceResponse:
    camera_entity_id = call.data["camera_entity_id"]
    file_path = call.data["file_path"]
    file_path_backup = call.data.get("file_path_backup")
    duration = min(call.data.get("duration", 40), 40)
    rotate_angle = call.data.get("rotate_angle")
    crop = call.data.get("crop")
    crop_aspect_ratio = call.data.get("crop_aspect_ratio")
    add_bar = call.data.get("add_bar", False)
    custom_text_left = call.data.get("custom_text_left", "")
    custom_text_middle = call.data.get("custom_text_middle", "")
    custom_text_right = call.data.get("custom_text_right", "")
    setting_font_path = call.data.get("setting_font_path")
    setting_font_size = call.data.get("setting_font_size", "auto")
    setting_font_color = call.data.get("setting_font_color", "black")
    setting_bar_height = call.data.get("setting_bar_height", "40")
    setting_bar_color = call.data.get("setting_bar_color", "white")
    setting_bar_position = call.data.get("setting_bar_position", "bottom")

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
    
    stream = await async_get_stream_source(hass, camera_entity_id)
    if not stream:
        return {"success": False, "error": "Camera stream could not be started"}

    try:
        probe = ffmpeg.probe(stream)
        video_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
        original_resolution = {
            "width": int(video_stream["width"]),
            "height": int(video_stream["height"])
        }
    except Exception:
        original_resolution = None

    stream_input = ffmpeg.input(
    stream, 
    rtsp_transport='tcp',
    timeout='5000000',
    max_delay='500000'
    )
    video = stream_input.video

    if rotate_angle:
            rotation_angle_rad = math.radians(rotate_angle)
            video = video.filter('rotate', rotation_angle_rad, fillcolor='black')
            _LOGGER.info(f"Rotated image by {rotate_angle} degrees")
    
    setting_font_color = sanitize_ffmpeg_color(setting_font_color)
    setting_bar_color = sanitize_ffmpeg_color(setting_bar_color)

    # CROP
    if crop and len(crop) >= 3:
        x, y, w = crop[:3]
        h = crop[3] if len(crop) == 4 else None
        if crop_aspect_ratio and not h:
            try:
                aspect_w, aspect_h = map(int, crop_aspect_ratio.split(":"))
                h = int(w * aspect_h / aspect_w)
            except:
                return {"success": False, "error": "Invalid aspect ratio format"}
        if h:
            video = video.crop(x=x, y=y, width=w, height=h)
            final_resolution = {"width": w, "height": h}

    # BAR + TEXT
    if add_bar and final_resolution:
        now = datetime.datetime.now().strftime("%d.%m.%y %H:%M:%S")

        try:
            if isinstance(setting_bar_height, str) and "%" in setting_bar_height:
                percent = float(setting_bar_height.strip("%")) / 100.0
                bar_height_px = int(final_resolution["height"] * percent)
            else:
                bar_height_px = int(setting_bar_height)
        except:
            bar_height_px = 80

        bar_y = final_resolution["height"] - bar_height_px if setting_bar_position == "bottom" else 0
        text_y = f"({bar_height_px}-text_h)/2 + {bar_y}"

        if setting_font_size == "auto":
            setting_font_size = max(10, int(bar_height_px * 0.5))
        else:
            setting_font_size = int(setting_font_size)
        
        custom_text_left = utf8_drawtext(custom_text_left)
        custom_text_middle = utf8_drawtext(custom_text_middle)
        custom_text_right = utf8_drawtext(custom_text_right)
       
        video = video.drawbox(
            x=0,
            y=bar_y,
            width="iw",
            height=bar_height_px,
            color=f"{setting_bar_color}",
            t="fill"
        )

        video = video.drawtext(
            text=custom_text_left,
            x=10,
            y=text_y,
            fontsize=setting_font_size,
            fontcolor=setting_font_color,
            fontfile=setting_font_path
        )

        video = video.drawtext(
            text=custom_text_middle,
            x="(w-text_w)/2",
            y=text_y,
            fontsize=setting_font_size,
            fontcolor=setting_font_color,
            fontfile=setting_font_path
        )

        video = video.drawtext(
            text=custom_text_right,
            x="w-text_w-10",
            y=text_y,
            fontsize=setting_font_size,
            fontcolor=setting_font_color,
            fontfile=setting_font_path
        )

    output_stream = ffmpeg.output(
        video,
        file_path,
        t=duration,
        vcodec="libx264",
        acodec="aac",
        crf=18,
        preset="medium",
        tune="film",          
        pix_fmt="yuv420p",
        format="mp4"
    )

        try:
        process = ffmpeg.run_async(
            output_stream,
            overwrite_output=True,
            pipe_stderr=True,
            pipe_stdout=True,  # optional, aber ok für communicate()
        )
    
        # communicate() blockt -> daher in den Executor
        stdout, stderr = await hass.async_add_executor_job(process.communicate)
    
        if process.returncode != 0:
            err_txt = (stderr or b"").decode("utf-8", errors="ignore")
            return {
                "success": False,
                "error": f"FFmpeg failed (rc={process.returncode}): {err_txt}"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"FFmpeg start error: {str(e)}"
        }

    if file_path_backup:
        try:
            os.makedirs(os.path.dirname(file_path_backup), exist_ok=True)

            # nicht über shell cp, sondern sauber kopieren (auch im Executor)
            await hass.async_add_executor_job(shutil.copy2, file_path, file_path_backup)

        except Exception as e:
            return {
                "success": False,
                "error": f"Backup failed: {str(e)}"
            }

    return {
        "success": True,
        "file_path": file_path,
        "backup_path": file_path_backup,
        "original_resolution": original_resolution,
        "final_resolution": final_resolution
    }


def sanitize_ffmpeg_color(color_str):
    color_str = color_str.strip().lower()
    if color_str.startswith("rgb(") and color_str.endswith(")"):
        r, g, b = map(int, color_str[4:-1].split(","))
        return f"0x{r:02X}{g:02X}{b:02X}"
    return color_str  

    
def utf8_drawtext(text: str) -> str:
    special_chars = {
        "°": "\\u00B0C",
        "ä": "\\u00E4",
        "ö": "\\u00F6",
        "ü": "\\u00FC",
        "Ä": "\\u00C4",
        "Ö": "\\u00D6",
        "Ü": "\\u00DC",
        "ß": "\\u00DF"
    }

    for char, unicode_escape in special_chars.items():
        text = text.replace(char, unicode_escape)

    return text.encode('utf-8').decode('unicode_escape')
    
def add_text_bar_old(img: Image.Image, custom_text_left: str, custom_text_middle: str,
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

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(setting_font_path, setting_font_size)
    except IOError:
        _LOGGER.warning(f"Font file not found: {setting_font_path}, using default font.")
        event_data["error"] = f"Font file not found: {setting_font_path}, using default font."
        font = ImageFont.load_default()

    # Draw bar background
    if setting_bar_position == "top":
        bar_rect = (0, 0, width, bar_height)
        text_y = (bar_height - setting_font_size) // 2
    else:
        bar_rect = (0, height - bar_height, width, height)
        text_y = height - bar_height + (bar_height - setting_font_size) // 2

    draw.rectangle(bar_rect, fill=setting_bar_color)

    margin = 10

    if custom_text_left:
        draw.text((margin, text_y), custom_text_left, fill=setting_font_color, font=font)

    if custom_text_middle:
        text_middle_width = draw.textlength(custom_text_middle, font=font)
        draw.text(((width - text_middle_width) // 2, text_y),
                  custom_text_middle, fill=setting_font_color, font=font)

    if custom_text_right:
        text_right_width = draw.textlength(custom_text_right, font=font)
        draw.text((width - text_right_width - margin, text_y),
                  custom_text_right, fill=setting_font_color, font=font)

    return img

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