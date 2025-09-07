# src/utils/course_loader.py
"""
Course data loader for loading course profiles from JSON files
"""

import json
from pathlib import Path
from typing import Optional

from ..models.course import CourseProfile, ClimbSegment, AltitudeEffects


def load_course_from_json(
    course_name: str, data_dir: Optional[str] = None
) -> CourseProfile:
    """
    Load course profile from JSON file

    Args:
        course_name: Name of the course file (without .json extension)
        data_dir: Optional custom data directory path

    Returns:
        CourseProfile object loaded from JSON

    Raises:
        FileNotFoundError: If course JSON file doesn't exist
        ValueError: If JSON file is invalid or missing required fields
    """
    # Default to src/data/courses directory
    if data_dir is None:
        current_dir = Path(__file__).parent.parent
        data_dir = current_dir / "data" / "courses"
    else:
        data_dir = Path(data_dir)

    # Construct file path
    json_path = data_dir / f"{course_name}.json"

    if not json_path.exists():
        raise FileNotFoundError(f"Course JSON file not found: {json_path}")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            course_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in course file {json_path}: {e}")

    # Validate required fields
    required_fields = [
        "name",
        "bike_distance_miles",
        "bike_elevation_gain_ft",
        "swim_distance_miles",
        "run_distance_miles",
        "run_elevation_gain_ft",
    ]

    for field in required_fields:
        if field not in course_data:
            raise ValueError(
                f"Required field '{field}' missing from course JSON"
            )

    # Convert key_climbs from dictionaries to ClimbSegment objects
    key_climbs = []
    if "key_climbs" in course_data:
        for climb_data in course_data["key_climbs"]:
            # Create ClimbSegment with available data
            climb = ClimbSegment(
                name=climb_data.get("name", "Unnamed Climb"),
                start_mile=climb_data.get("start_mile", 0.0),
                length_miles=climb_data.get("length_miles", 0.0),
                avg_grade=climb_data.get("avg_grade", 0.0),
                max_grade=climb_data.get("max_grade", 0.0),
                elevation_gain_ft=climb_data.get("elevation_gain_ft", 0),
                start_coords=climb_data.get("start_coords"),
                end_coords=climb_data.get("end_coords"),
                gps_points=climb_data.get("gps_points"),
            )
            key_climbs.append(climb)

    # Parse altitude_effects if present
    altitude_effects = None
    if "altitude_effects" in course_data:
        altitude_data = course_data["altitude_effects"]
        altitude_effects = AltitudeEffects(
            base_altitude_ft=altitude_data.get("base_altitude_ft", 0),
            max_altitude_ft=altitude_data.get("max_altitude_ft", 0),
            altitude_zone=altitude_data.get("altitude_zone", "sea_level"),
            oxygen_reduction_percent=altitude_data.get(
                "oxygen_reduction_percent", 0.0
            ),
            performance_impact=altitude_data.get("performance_impact", ""),
            acclimatization_needed=altitude_data.get(
                "acclimatization_needed", False
            ),
            hydration_multiplier=altitude_data.get(
                "hydration_multiplier", 1.0
            ),
        )

    # Create CourseProfile object
    course_profile = CourseProfile(
        name=course_data["name"],
        bike_distance_miles=course_data["bike_distance_miles"],
        bike_elevation_gain_ft=course_data["bike_elevation_gain_ft"],
        swim_distance_miles=course_data["swim_distance_miles"],
        run_distance_miles=course_data["run_distance_miles"],
        run_elevation_gain_ft=course_data["run_elevation_gain_ft"],
        key_climbs=key_climbs,
        technical_sections=course_data.get("technical_sections", []),
        altitude_ft=course_data.get("altitude_ft", 0),
        surface_types=course_data.get("surface_types", []),
        altitude_effects=altitude_effects,
        start_coords=course_data.get("start_coords"),
        finish_coords=course_data.get("finish_coords"),
        elevation_profile=course_data.get("elevation_profile", []),
        gps_metadata=None,  # JSON doesn't contain metadata object
    )

    return course_profile


def get_available_courses(data_dir: Optional[str] = None) -> list[str]:
    """
    Get list of available course names from the data directory

    Args:
        data_dir: Optional custom data directory path

    Returns:
        List of available course names (without .json extension)
    """
    # Default to src/data/courses directory
    if data_dir is None:
        current_dir = Path(__file__).parent.parent
        data_dir = current_dir / "data" / "courses"
    else:
        data_dir = Path(data_dir)

    if not data_dir.exists():
        return []

    # Find all JSON files and return names without extension
    course_names = []
    for json_file in data_dir.glob("*.json"):
        course_names.append(json_file.stem)

    return sorted(course_names)


# Predefined course loaders for convenience
def load_happy_valley_70_3() -> CourseProfile:
    """Load the Happy Valley 70.3 course profile (research-based)"""
    return load_course_from_json("happy_valley_70_3_real")


def load_happy_valley_70_3_gps() -> CourseProfile:
    """Load the Happy Valley 70.3 course profile (GPS-based)"""
    return load_course_from_json("im70.3_pennstate")


def load_alpe_dhuez() -> CourseProfile:
    """Load the Alpe d'Huez triathlon course profile"""
    return load_course_from_json("alpedhuez_triathlon")


def load_alpe_dhuez_real() -> CourseProfile:
    """Load Alpe d'Huez real course with 4 major climbs and 21-bend ascent"""
    return load_course_from_json("alpe_dhuez_real")


# Generic loader for any course by name
def load_course(course_name: str) -> CourseProfile:
    """
    Load any available course by name

    Args:
        course_name: Name of the course (without .json extension)

    Returns:
        CourseProfile object
    """
    return load_course_from_json(course_name)
