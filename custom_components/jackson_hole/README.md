# Jackson Hole Mountain Resort Integration

Home Assistant integration for Jackson Hole Mountain Resort data.

## Features

- Real-time lift and trail status
- Snow conditions and weather forecasts
- Webcam feeds
- Summer hiking/biking trail information

## Installation

### Manual Installation

1. Copy the `jackson_hole` folder to your `custom_components/` directory
2. Restart Home Assistant
3. Add the integration via Settings → Devices & Services → Add Integration

## Configuration

The integration uses a GUI-based configuration flow. No YAML configuration is required.

### Options

- **API URL**: Default works for most users
- **Update Interval**: 5-60 minutes (default: 15)
- **Entity Creation**: Choose which entity types to create:
  - Individual lift entities (13 lifts)
  - Individual trail entities (130+ trails) - OFF by default
  - Summer trail entities (hiking/biking)
  - Weather entity with forecast
  - Webcam camera entities

## Entities

### Sensors

- Snow depth (mid-mountain and summit)
- Recent snowfall (24h, 48h, 7day)
- Temperature (base, mid, summit)
- Wind speed (base, mid, summit)
- Lift and trail counts
- Trail breakdown by difficulty

### Binary Sensors (Optional)

- Individual lift status (13 lifts)
- Individual trail status (130+ trails)
- Summer hiking trails
- Summer bike trails

### Weather

- Current conditions
- 6-day forecast

### Cameras

- Multiple webcam feeds

## Troubleshooting

### No Data Appearing

- Check Home Assistant logs
- Verify API URL is correct
- Check internet connection

### Too Many Entities

- Disable trail entities in configuration
- Only enable needed entity types

## Support

- [GitHub Issues](https://github.com/yourusername/hass-jackson-hole/issues)
- [Home Assistant Community](https://community.home-assistant.io)

## License

MIT License
