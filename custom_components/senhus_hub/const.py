DOMAIN = "senhus_hub"
MANUFACTURER = "Senhus"
MODEL_HUB1 = "Hub1"
PROJECT_NAME_PREFIX = "Senhus"

DEFAULT_PORT = 6053

# Slot identifiers
SLOT_LEFT = "slot_left"
SLOT_RIGHT_TOP = "slot_right_top"
SLOT_RIGHT_BOTTOM = "slot_right_bottom"
ALL_SLOTS = [SLOT_LEFT, SLOT_RIGHT_TOP, SLOT_RIGHT_BOTTOM]

# Per-slot config keys
CONF_ENTITY_ID = "entity_id"
CONF_LABEL = "label"
CONF_UNIT = "unit"

# Card types
CARD_CUSTOM = "custom"
CONF_CARD_TYPE = "card_type"

# Layout
CONF_LAYOUT = "layout"
LAYOUT_DEFAULT = "default"
LAYOUT_THREE_ROWS = "three_rows"
ALL_LAYOUTS = [LAYOUT_DEFAULT, LAYOUT_THREE_ROWS]

# ESPHome text entity names expected on the device
ESP_ENTITY_SLOT_VALUE = "slot{n}_value"
ESP_ENTITY_SLOT_LABEL = "slot{n}_label"
ESP_ENTITY_SLOT_UNIT = "slot{n}_unit"
ESP_ENTITY_LAYOUT = "display_layout"

# GitHub
GITHUB_REPO = "Senhus-DK/senhus_hub"
GITHUB_API_RELEASES = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
FIRMWARE_ASSET_NAME = "firmware.ota.bin"
