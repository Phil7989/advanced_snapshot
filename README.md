
# Advanced Snapshot for Home Assistant

![Advanced Snapshot Icon](https://img.icons8.com/ios/452/camera.png)  
**Advanced Snapshot** ist eine benutzerdefinierte Integration für [Home Assistant](https://www.home-assistant.io/), die es ermöglicht, automatisch Schnappschüsse von Kameras zu erstellen und diese mit benutzerdefinierten Texten und Optionen zu versehen. Diese Integration bietet zusätzliche Flexibilität und Anpassbarkeit für Kamerabilder, die in Home Assistant verwendet werden.

## Features

- **Capture snapshots** from any camera in your Home Assistant setup.
- **Add custom text** to the snapshots, with options for left, center, and right-aligned text.
- **Add a customizable bar** to the snapshot (position, color, height, etc.).
- **Crop images** before saving them.
- **Save snapshots** to a specified path and optionally create backups.

## Installation

### Prerequisites

Ensure you have a working Home Assistant setup and that you have the necessary permissions to install custom integrations.

1. Download the custom integration folder.
2. Place the folder in your Home Assistant configuration directory:  
   `config/custom_components/advanced_snapshot/`

3. Restart Home Assistant.

### Configuration

Add the following configuration to your `configuration.yaml` file:

```yaml
# Advanced Snapshot Configuration
advanced_snapshot:
  # Optional: Add custom settings if needed
```

Alternatively, you can configure the service via the Home Assistant UI under **Configuration** > **Integrations**.

## Usage

After installation, you can use the `advanced_snapshot` service to take snapshots from your camera entities. To call the service, use the following YAML:

```yaml
service: advanced_snapshot.take_snapshot
data:
  camera_entity_id: camera.your_camera
  file_path: /config/www/snapshot.jpg
  file_path_backup: /config/www/snapshot_backup.jpg
  crop: [100, 100, 400, 300]  # (x, y, width, height)
  add_bar: true
  custom_text_left: "Left Text"
  custom_text_middle: "Center Text"
  custom_text_right: "Right Text"
  setting_font_path: "/config/custom_components/advanced_snapshot/Arial Bold.ttf"
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
- **setting_font_path** (Optional): Path to the font file (defaults to `/config/custom_components/advanced_snapshot/Arial Bold.ttf`).
- **setting_font_size** (Optional): Font size for the text (default is 20).
- **setting_font_color** (Optional): Color of the text (default is `black`).
- **setting_bar_height** (Optional): Height of the bar (default is 40).
- **setting_bar_color** (Optional): Color of the bar (default is `white`).
- **setting_bar_position** (Optional): Position of the bar (`top` or `bottom`).

## Example

Here's an example of using the integration to capture a snapshot from your camera with a custom bar and text:

```yaml
service: advanced_snapshot.take_snapshot
data:
  camera_entity_id: camera.front_door
  file_path: /config/www/front_door_snapshot.jpg
  file_path_backup: /config/www/front_door_snapshot_backup.jpg
  crop: [50, 50, 800, 600]
  add_bar: true
  custom_text_left: "Front Door"
  custom_text_middle: "Snapshot"
  custom_text_right: "{{ now() }}"
  setting_font_size: 18
  setting_font_color: "white"
  setting_bar_height: 50
  setting_bar_color: "blue"
  setting_bar_position: "top"
```

## Troubleshooting

If the service does not work as expected, please ensure the following:

- The **camera_entity_id** is correct and the camera is functioning properly.
- The **file_path** is accessible and Home Assistant has permission to write to the directory.
- Ensure you are using the correct image file formats (e.g., PNG, JPG).
- If you're receiving errors with the text bar, verify the font file path and font size.

## Contributing

If you find a bug or would like to contribute new features, please fork the repository and submit a pull request. Contributions are always welcome!

## Donate

If you find this integration useful and want to support its development, feel free to make a donation:

[![Donate](https://img.shields.io/badge/Donate-PayPal-blue)](https://paypal.me/PhilippArnold89)

Your support is greatly appreciated!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
