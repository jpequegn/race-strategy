# src/models/course.py
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ClimbSegment:
    """Individual climb within a course"""
    name: str
    start_mile: float
    length_miles: float
    avg_grade: float
    max_grade: float
    elevation_gain_ft: int

@dataclass
class CourseProfile:
    """Complete race course profile"""
    name: str
    bike_distance_miles: float
    bike_elevation_gain_ft: int
    swim_distance_miles: float
    run_distance_miles: float
    run_elevation_gain_ft: int
    key_climbs: List[ClimbSegment]
    technical_sections: List[str]
    surface_types: List[str] = None
    altitude_ft: int = 0
