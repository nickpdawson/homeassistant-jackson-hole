"""Constants for the Jackson Hole Mountain Resort integration."""

DOMAIN = "jackson_hole"
NAME = "Jackson Hole Mountain Resort"
MANUFACTURER = "Jackson Hole Mountain Resort"
MODEL = "Mountain data API"

# Before 2.0.0 every entity used this device identifier. Keeping it keeps
# the device id, so device triggers and actions in automations still work.
DEVICE_IDENTIFIER = "jackson_hole_resort"

DEFAULT_API_URL = "https://jacksonhole-prod.zaneray.com/api/all.json"
FETCH_TIMEOUT = 15  # seconds

# all.json is about 75 KB. Anything far larger is not the resort feed.
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
# Pano cam stills are about 500 KB.
MAX_IMAGE_BYTES = 10 * 1024 * 1024
# The webcams refresh every few minutes; don't refetch on every frontend poll.
IMAGE_CACHE_SECONDS = 60

# Forecast dates carry no zone; they are resort local days.
RESORT_TIME_ZONE = "America/Denver"

CONF_API_URL = "api_url"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_CREATE_LIFT_ENTITIES = "create_lift_entities"
CONF_CREATE_TRAIL_ENTITIES = "create_trail_entities"
CONF_CREATE_SUMMER_ENTITIES = "create_summer_entities"
CONF_CREATE_WEATHER_ENTITY = "create_weather_entity"
CONF_CREATE_WEBCAM_ENTITIES = "create_webcam_entities"

DEFAULT_UPDATE_INTERVAL = 15  # minutes
MIN_UPDATE_INTERVAL = 5
MAX_UPDATE_INTERVAL = 60

DEFAULTS = {
    CONF_API_URL: DEFAULT_API_URL,
    CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
    CONF_CREATE_LIFT_ENTITIES: True,
    # About 145 trails, so off unless asked for.
    CONF_CREATE_TRAIL_ENTITIES: False,
    CONF_CREATE_SUMMER_ENTITIES: True,
    CONF_CREATE_WEATHER_ENTITY: True,
    CONF_CREATE_WEBCAM_ENTITIES: True,
}

TRAIL_DIFFICULTY = {
    "GREEN_CIRCLE": {"name": "Beginner", "icon": "mdi:ski-water"},
    "BLUE_SQUARE": {"name": "Intermediate", "icon": "mdi:ski"},
    "DOUBLE_BLUE_SQUARE": {"name": "Advanced Intermediate", "icon": "mdi:ski"},
    "BLACK_DIAMOND": {"name": "Advanced", "icon": "mdi:slope-downhill"},
    "DOUBLE_BLACK_DIAMOND": {"name": "Expert", "icon": "mdi:terrain"},
    "TERRAIN_PARKS": {"name": "Terrain Park", "icon": "mdi:snowboard"},
    # Summer levels
    "GREEN": {"name": "Easy", "icon": "mdi:walk"},
    "BLUE": {"name": "Moderate", "icon": "mdi:hiking"},
    "BLACK": {"name": "Strenuous", "icon": "mdi:terrain"},
    "YELLOW": {"name": "E-Bike Allowed", "icon": "mdi:bike-electric"},
}

LIFT_ICONS = {
    "TRAM": "mdi:gondola",
    "GONDOLA": "mdi:gondola",
    "DETACHABLE_CHAIRLIFT": "mdi:ski-lift",
    "CHAIRLIFT": "mdi:ski-lift",
    "FIXED_GRIP_CHAIRLIFT": "mdi:ski-lift",
    "SURFACE_LIFT": "mdi:ski",
}

# Feed icon class -> HA weather condition.
WEATHER_CONDITION_MAP = {
    "icon-svg_sun": "sunny",
    "icon-svg_sunny": "sunny",
    "icon-svg_clear": "sunny",
    "icon-svg_partlycloudy": "partlycloudy",
    "icon-svg_cloudy": "cloudy",
    "icon-svg_lightsnow": "snowy",
    "icon-svg_heavysnow": "snowy",
    "icon-svg_rain": "rainy",
    "icon-svg_thunderstorm": "lightning-rainy",
}

ATTRIBUTION = "Data provided by Jackson Hole Mountain Resort"
