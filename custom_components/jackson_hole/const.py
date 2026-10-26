"""Constants for Jackson Hole Mountain Resort integration."""
# Integration identification
DOMAIN = "jackson_hole"
NAME = "Jackson Hole Mountain Resort"
MANUFACTURER = "Jackson Hole Mountain Resort"
MODEL = "Mountain Data API"

# API Configuration
DEFAULT_API_URL = "https://jacksonhole-prod.zaneray.com/api/all.json"
API_TIMEOUT = 10  # seconds

# Configuration keys
CONF_API_URL = "api_url"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_CREATE_LIFT_ENTITIES = "create_lift_entities"
CONF_CREATE_TRAIL_ENTITIES = "create_trail_entities"
CONF_CREATE_SUMMER_ENTITIES = "create_summer_entities"
CONF_CREATE_WEATHER_ENTITY = "create_weather_entity"
CONF_CREATE_WEBCAM_ENTITIES = "create_webcam_entities"

# Default values
DEFAULT_UPDATE_INTERVAL = 15  # minutes
MIN_UPDATE_INTERVAL = 5
MAX_UPDATE_INTERVAL = 60
DEFAULT_CREATE_LIFT_ENTITIES = True
DEFAULT_CREATE_TRAIL_ENTITIES = False  # Too many by default
DEFAULT_CREATE_SUMMER_ENTITIES = True
DEFAULT_CREATE_WEATHER_ENTITY = True
DEFAULT_CREATE_WEBCAM_ENTITIES = True

# Trail difficulty mapping
TRAIL_DIFFICULTY = {
    "GREEN_CIRCLE": {
        "name": "Beginner",
        "icon": "mdi:ski-water",
        "color": "green"
    },
    "BLUE_SQUARE": {
        "name": "Intermediate",
        "icon": "mdi:ski",
        "color": "blue"
    },
    "DOUBLE_BLUE_SQUARE": {
        "name": "Advanced Intermediate",
        "icon": "mdi:ski",
        "color": "blue"
    },
    "BLACK_DIAMOND": {
        "name": "Advanced",
        "icon": "mdi:slope-downhill",
        "color": "black"
    },
    "DOUBLE_BLACK_DIAMOND": {
        "name": "Expert",
        "icon": "mdi:terrain",
        "color": "black"
    },
    "TERRAIN_PARKS": {
        "name": "Terrain Park",
        "icon": "mdi:snowboard",
        "color": "orange"
    },
    # Summer levels
    "GREEN": {
        "name": "Easy",
        "icon": "mdi:walk",
        "color": "green"
    },
    "BLUE": {
        "name": "Moderate",
        "icon": "mdi:hiking",
        "color": "blue"
    },
    "BLACK": {
        "name": "Strenuous",
        "icon": "mdi:terrain",
        "color": "black"
    },
    "YELLOW": {
        "name": "E-Bike Allowed",
        "icon": "mdi:bike-electric",
        "color": "yellow"
    },
}

# Lift type mapping
LIFT_TYPE = {
    "TRAM": {
        "name": "Aerial Tramway",
        "icon": "mdi:ski-lift"
    },
    "GONDOLA": {
        "name": "Gondola",
        "icon": "mdi:gondola"
    },
    "DETACHABLE_CHAIRLIFT": {
        "name": "High-Speed Chairlift",
        "icon": "mdi:chair-rolling"
    },
    "FIXED_GRIP_CHAIRLIFT": {
        "name": "Fixed Chairlift",
        "icon": "mdi:chair-rolling"
    },
    "SURFACE_LIFT": {
        "name": "Surface Lift",
        "icon": "mdi:ski"
    },
}

# Opening status mapping
OPENING_STATUS_MAP = {
    "OPEN": "open",
    "CLOSED": "closed",
    "OUT_OF_PERIOD": "closed",
    "HOLD": "hold",
}

# Weather condition mapping for Home Assistant
WEATHER_CONDITION_MAP = {
    "icon-svg_heavysnow": "snowy-rainy",
    "icon-svg_lightsnow": "snowy",
    "icon-svg_partlycloudy": "partlycloudy",
    "icon-svg_cloudy": "cloudy",
    "icon-svg_sunny": "sunny",
    "icon-svg_clear": "clear-night",
    "icon-svg_thunderstorm": "lightning-rainy",
    "icon-svg_rain": "rainy",
}

# Attribution
ATTRIBUTION = "Data provided by Jackson Hole Mountain Resort"
