# src/models/course.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime


@dataclass
class GPSPoint:
    """Individual GPS data point with coordinates and elevation"""

    latitude: float
    longitude: float
    elevation_ft: float
    distance_miles: float
    gradient_percent: Optional[float] = None


@dataclass
class ClimbSegment:
    """Individual climb within a course"""

    name: str
    start_mile: float
    length_miles: float
    avg_grade: float
    max_grade: float
    elevation_gain_ft: int
    # GPS metadata
    start_coords: Optional[Tuple[float, float]] = None  # (lat, lon)
    end_coords: Optional[Tuple[float, float]] = None
    gps_points: List[GPSPoint] = field(default_factory=list)


@dataclass
class GPSMetadata:
    """GPS data quality and source information"""

    source_file: Optional[str] = None
    total_points: int = 0
    missing_elevation_points: int = 0
    data_quality_score: float = 0.0  # 0-100 scale
    smoothed: bool = False
    parsed_at: Optional[datetime] = None
    bounds: Optional[Dict[str, float]] = None  # min/max lat/lon

    # Coordinate validation results
    invalid_latitude_points: int = 0
    invalid_longitude_points: int = 0
    invalid_elevation_points: int = 0
    large_distance_jumps: int = 0
    total_validation_errors: int = 0


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

    # GPS-specific fields
    gps_metadata: Optional[GPSMetadata] = None
    elevation_profile: List[GPSPoint] = field(default_factory=list)
    start_coords: Optional[Tuple[float, float]] = None
    finish_coords: Optional[Tuple[float, float]] = None
