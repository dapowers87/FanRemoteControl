from enum import Enum

class FanSpeedState(Enum):
    OFF = 0
    ON = 1

class FanSpeed(Enum):
    OFF = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class FanLight(Enum):
    OFF = 0
    ON = 1
