# Jackson Hole Mountain Resort for Home Assistant

A custom integration that reads Jackson Hole Mountain Resort's public
mountain data feed and turns it into Home Assistant entities: snow depth
and snowfall, temperature and wind at three spots on the mountain, lift
and trail status, summer trails, a daily forecast and the resort webcams.

The data comes from `https://jacksonhole-prod.zaneray.com/api/all.json`,
the feed behind the resort's own mountain report page. This project is not
affiliated with Jackson Hole Mountain Resort.

Requires Home Assistant 2025.12 or newer. Tested on 2026.10.

## Install with HACS

1. In HACS, open the menu (three dots, top right) and pick **Custom repositories**.
2. Add `https://github.com/nickpdawson/homeassistant-jackson-hole` with type **Integration**.
3. Search HACS for **Jackson Hole Mountain Resort** and download it.
4. Restart Home Assistant.

To install by hand, copy `custom_components/jackson_hole` into your
`config/custom_components/` folder and restart.

## Setup

Go to **Settings > Devices & services > Add integration** and pick
**Jackson Hole Mountain Resort**. The form asks for:

- **API URL**: leave the default unless the resort moves its feed. Must be https.
- **Update interval**: 5 to 60 minutes, default 15.
- **Create an entity for each lift**: 13 binary sensors. On by default.
- **Create an entity for each trail**: about 145 binary sensors. Off by default.
- **Create summer hiking and bike trail entities**: two count sensors, plus
  one binary sensor per summer trail when the resort lists them. On by default.
- **Create a weather entity**: on by default.
- **Create a camera for each webcam**: 7 cameras today. On by default.

Setup fetches the feed once and stops with an error if it cannot read it.
Only one entry is allowed. YAML setup is not supported.

## Options

**Settings > Devices & services > Jackson Hole Mountain Resort > Configure**
changes the same settings. Saving reloads the integration. Turning a group
off removes its entities.

## Entities

All entities sit on one device, **Jackson Hole Mountain Resort**. Ids
below are what a new install gets; an upgraded install keeps its own.

| Entity | Example id | State |
| --- | --- | --- |
| Snow depth mid-mountain, summit | `sensor.jackson_hole_mountain_resort_snow_depth_mid_mountain` | in |
| 24, 48 hour and 7 day snowfall | `sensor.jackson_hole_mountain_resort_24_hour_snowfall` | in, mid-mountain |
| Temperature base, mid-mountain, summit | `sensor.jackson_hole_mountain_resort_temperature_summit` | °F |
| Wind base, mid-mountain, summit | `sensor.jackson_hole_mountain_resort_wind_summit` | mph |
| Lift status | `sensor.jackson_hole_mountain_resort_lift_status` | lifts open; attributes give totals |
| Trail status | `sensor.jackson_hole_mountain_resort_trail_status` | trails open; attributes give groomed and park counts |
| Trails by difficulty | `sensor.jackson_hole_mountain_resort_trails_by_difficulty` | total trails; attributes count total, open and groomed per level |
| Last snowfall | `sensor.jackson_hole_mountain_resort_last_snowfall` | date |
| Last update | `sensor.jackson_hole_mountain_resort_last_update` | time the feed was generated |
| Summer hiking and bike trails | `sensor.jackson_hole_mountain_resort_summer_hiking_trails` | trails open |
| Each lift | `binary_sensor.jackson_hole_mountain_resort_lift_aerial_tram` | on when running |
| Each trail | `binary_sensor.jackson_hole_mountain_resort_trail_nez_perce` | on when open |
| Weather | `weather.jackson_hole_mountain_resort_weather` | mid-mountain readings, daily forecast |
| Each webcam | `camera.jackson_hole_mountain_resort_webcam_cody_bowl` | still image |

The weather entity's condition is today's forecast icon; the feed has no
current condition. Its temperature and wind are live mid-mountain readings.
Get the forecast with the `weather.get_forecasts` action and `type: daily`.

Webcam images are cached for 60 seconds. Small cards get the feed's
thumbnail instead of the full image.

## Troubleshooting

Turn on debug logging in `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.jackson_hole: debug
```

Or use **Download diagnostics** on the integration page. It includes the
settings and the last feed response.

- **Feed outage**: entities go unavailable and come back on the next good
  fetch. If the feed is down when Home Assistant starts, setup retries on
  its own.
- **Off season**: the feed keeps publishing with everything closed, so
  lift and trail sensors read off and counts read 0. Values the resort
  leaves blank show as unknown.
- **A lift, trail or webcam shows unavailable**: the resort removed or
  renamed it in the feed. Delete the entity if it does not come back.
- **Too many entities**: turn off trail entities in the options.

## Breaking changes in 2.0.0

- Minimum Home Assistant version is 2025.12.
- Unique ids now belong to the config entry. Existing entities are
  migrated on first start, so entity ids, history and customizations carry
  over. The device keeps its id, so device automations keep working.
- Webcams are matched by caption instead of list position. A webcam whose
  old position is past the end of today's list is not migrated.
- Missing values show as unknown instead of 0. For example, 7 day snowfall
  at mid-mountain is blank in the feed today.
- Last snowfall works again. Before 2.0.0 it raised an error on every
  update and never had a state.
- The weather forecast works again through `weather.get_forecasts`. The
  icon `icon-svg_sun` now maps to sunny, heavy snow to snowy, and unknown
  icons give no condition instead of cloudy.
- Snowfall sensors use the precipitation device class. Trail binary
  sensors use the opening device class, so they show Open and Closed
  instead of Running and Not running. Counts have a measurement state
  class, so they get long-term statistics.
- Entity names are in sentence case, for example "Snow depth summit".
  Entity ids do not change.
- Lift and trail attributes drop values the feed sends as 0, and numbers
  lose their thousands separator ("6000 ft", not "6,000 ft"). The weather
  entity shows snow as "40 in".
- Changes in the options dialog are saved to the entry's options. Before
  2.0.0 the dialog failed to open on current Home Assistant.

## License

CC0 1.0 Universal. See [LICENSE](LICENSE).
