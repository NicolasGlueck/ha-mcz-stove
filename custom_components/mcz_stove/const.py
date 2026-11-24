"""Constants for the MCZ Pellet Stove (pre-Maestro) integration."""
from datetime import timedelta

DOMAIN = "mcz_stove"
DEFAULT_PORT = 5001
DEFAULT_NAME = "Pellet stove"
DEFAULT_NAME_DE = "Pelletofen"

SCAN_INTERVAL = timedelta(seconds=15)
# INFR (firmware, Wi-Fi signal) is only read on every n-th poll to save connections
INFO_EVERY = 20
# Number entities collect quick taps: a command is sent only after this quiet period
DEBOUNCE_SECONDS = 1.0
# How long a number/switch shows its requested value while the stove has not reported it yet
PENDING_TIMEOUT = 45

# State code (DATR0 field 5) -> translation key
STATES = {
    0: "off",
    1: "ignition_1", 2: "ignition_2", 3: "ignition_3", 4: "ignition_4",
    5: "ignition_5", 6: "ignition_6", 7: "ignition_7",
    8: "heating",
    9: "shutdown_1", 10: "shutdown_2",
    11: "eco_stop_1", 12: "eco_stop_2", 13: "eco_stop_3",
    14: "pellets_low", 15: "pellets_empty", 16: "power_failure", 17: "frost_protection",
    60: "ignition_failed", 61: "no_pellets", 69: "door_open",
}
STATE_UNKNOWN = "unknown"
# pellets low/empty, power failure and the 50..99 range that the HottoH app shows as alarms
PROBLEM_CODES = {14, 15, 16, *range(50, 100)}

# Fields of the DATR0 response
F_STATE = 5
F_POWER = 6
F_ECO = 7
F_TIMER = 8
F_ROOM_TEMP = 9  # 0.1 °C
F_TARGET_TEMP = 10  # 0.1 °C
F_EXHAUST_TEMP = 21  # 0.1 °C
F_POWER_PERCENT = 22  # actual power in %, level 1 = 20 %
F_LEVEL_SET = 23
F_LEVEL_MIN = 24
F_LEVEL_MAX = 25
F_EXHAUST_FAN = 26  # rpm
MIN_FIELDS = F_EXHAUST_FAN + 1


def fan_fields(nr: int) -> tuple[int, int, int]:
    """Field indices (actual, setpoint, maximum) of fan 1..3."""
    return 24 + 3 * nr, 25 + 3 * nr, 26 + 3 * nr


def has_fan(fields: list[int], nr: int) -> bool:
    """A fan exists if the stove reports it with a maximum above 0."""
    idx_max = fan_fields(nr)[2]
    return len(fields) > idx_max and fields[idx_max] > 0


# Write parameters (DATW)
P_POWER = 0
P_LEVEL = 2
P_FAN_BASE = 4  # fan n -> 4 + n
