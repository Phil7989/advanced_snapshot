# <img src="https://raw.githubusercontent.com/Phil7989/advanced_snapshot/refs/heads/main/images/icon.png" height="60"> Advanced Snapshot for Home Assistant

**Advanced Snapshot** is a custom integration for [Home Assistant](https://www.home-assistant.io/) that allows you to automatically capture snapshots from cameras and customize them with personalized texts and crop options. This integration provides additional flexibility and customization for camera images used in Home Assistant.

| <img src="https://github.com/Phil7989/advanced_snapshot/blob/main/images/original.jpg" alt="Original Snapshot" width="500"> | <img src="https://github.com/Phil7989/advanced_snapshot/blob/main/images/advancedsnapshot.jpg" alt="Advanced Snapshot" width="500"> |
|-----------------------------|-----------------------------|
| Original Snapshot           | Advanced Snapshot           |

## 🚀 Features

- **Capture snapshots** from any camera in your Home Assistant setup.
- **Add custom text** to the snapshots, with options for left, center, and right-aligned text.
- **Add a customizable bar** to the snapshot (position, color, height, etc.).
- **Crop images** before saving them.
- **Save snapshots** to a specified path and optionally create backups.

## 🔧 Installation - Using HACS

This integration is NO official HACS Integration right now.

Open HACS then install the "advanced_snapshot" integration or use the link below.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Phil7989&repository=advanced_snapshot&category=integration)

If you use this method, your component will always update to the latest version.

### Configuration

Go to Configuration -> Integrations and click on "add integration". Then search for "advanced_snapshot".

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=advanced_snapshot)

## 🔧 Usage

After installation, you can use the `advanced_snapshot` service to take snapshots from your camera entities. To call the service, use the following YAML:

```yaml
service: advanced_snapshot.take_snapshot
data:
  camera_entity_id: camera.your_camera_front_door
  file_path: /config/www/frontdoor.jpg
  file_path_backup: >-
    /config/www/backupsnapshots/{{ now().strftime('%y%m%d')}}_{{
    now().strftime('%H%M%S')}}_frontdoor.jpg
  crop: [100, 100, 400, 300]  # (x, y, width, height)
  add_bar: true
  custom_text_left: "Front Door"
  custom_text_middle: "{{ states('sensor.garten_actual_temperature') }} °C"
  custom_text_right: "{{ now().strftime('%d.%m.%y %H:%M:%S') }}"
  setting_font_path: "/config/custom_components/advanced_snapshot/Arial.ttf"
  setting_font_size: 20
  setting_font_color: "black"
  setting_bar_height: 40
  setting_bar_color: "white"
  setting_bar_position: "bottom"
```

### Parameters

- **camera_entity_id** (Required): The entity ID of the camera you want to capture a snapshot from.
- **file_path** (Required): The path where the snapshot will be saved.
- **file_path_backup** (Optional): A backup path where a copy of the snapshot will be saved.
- **crop** (Optional): List with four integers `[x, y, width, height]` to crop the image. If not provided, the full image will be used.
- **add_bar** (Optional): If set to `true`, a text bar will be added to the snapshot.
- **custom_text_left**, **custom_text_middle**, **custom_text_right** (Optional): Texts to be displayed on the left, center, and right of the bar.
- **setting_font_path** (Optional): Path to the font file (defaults to `/config/custom_components/advanced_snapshot/Arial.ttf`).
- **setting_font_size** (Optional): Font size for the text (default is 20).
- **setting_font_color** (Optional): Color of the text (default is `black`).
- **setting_bar_height** (Optional): Height of the bar (default is 40).
- **setting_bar_color** (Optional): Color of the bar (default is `white`).
- **setting_bar_position** (Optional): Position of the bar (`top` or `bottom`).

### Response

```
success: true
file_path: /config/www/push/snapshot.jpg
backup_path: /config/www/backupsnapshots/250216_220954_snapshot.jpg
original_resolution:
  - 3840
  - 2160
final_resolution:
  - 1066
  - 640
error: null
```

## 💡 Troubleshooting

If the service does not work as expected, please ensure the following:

- The **camera_entity_id** is correct and the camera is functioning properly.
- The **file_path** is accessible and Home Assistant has permission to write to the directory.
- Ensure you are using the correct image file formats (e.g., PNG, JPG).
- If you're receiving errors with the text bar, verify the font file path and font size.

## Contributing

If you find a bug or would like to contribute new features, please fork the repository and submit a pull request. Contributions are always welcome!

## 🙏 Donate

If you find this integration useful and want to support its development, feel free to make a donation:

[![Donate](https://img.shields.io/badge/Donate-PayPal-blue)](https://paypal.me/PhilippArnold89)
<a href='https://www.buymeacoffee.com/56xsp4m6sxy'><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="BuyMeACoffee" width="80" style="width:80px; height:auto;"></a>

Your support is greatly appreciated!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
