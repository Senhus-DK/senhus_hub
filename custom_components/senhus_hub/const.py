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
# Future: CARD_ENERGY = "energy"
# Future: CARD_WEATHER = "weather"
CONF_CARD_TYPE = "card_type"

# Layout
CONF_LAYOUT = "layout"
LAYOUT_DEFAULT = "default"
# Future: LAYOUT_THREE_PANEL = "three_panel"

# ESPHome text entity names expected on the device
# The firmware exposes: slot1_value, slot1_label, slot1_unit, slot2_*, slot3_*
ESP_ENTITY_SLOT_VALUE = "slot{n}_value"
ESP_ENTITY_SLOT_LABEL = "slot{n}_label"
ESP_ENTITY_SLOT_UNIT = "slot{n}_unit"

# GitHub
GITHUB_REPO = "Senhus-DK/hacs-senhus-hub"
GITHUB_API_RELEASES = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
FIRMWARE_ASSET_NAME = "firmware.ota.bin"
