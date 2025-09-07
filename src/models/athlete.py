from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AthleteProfile:
    """Individual athlete capabilities and goals"""

    name: str
    ftp_watts: int
    swim_pace_per_100m: float  # seconds
    run_threshold_pace: float  # minutes per mile
    experience_level: str  # "beginner", "intermediate", "advanced"
    previous_70_3_time: Optional[str]  # "HH:MM:SS"
    strengths: List[str]  # ["swim", "bike", "run"]
    limiters: List[str]
    target_finish_time: Optional[str]
    weight_lbs: float = 150
    height_inches: float = 70
    age: int = 35
