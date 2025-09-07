from dataclasses import dataclass
from typing import Optional

@dataclass
class RaceConditions:
    """Environmental conditions for race day"""
    temperature_f: int
    wind_speed_mph: int
    wind_direction: str  # "headwind", "tailwind", "crosswind", "variable"
    precipitation: str  # "none", "light", "moderate", "heavy"
    humidity_percent: int
    cloud_cover: str = "mixed"  # "clear", "partial", "overcast"
    water_temp_f: Optional[int] = None
