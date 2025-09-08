#!/usr/bin/env python3
"""
GPS Parser Demo Script

Demonstrates basic usage of the GPS parser with example GPX files.
Shows how to load, parse, and analyze GPS course data.

Usage:
    python examples/gps_demo.py

Dependencies:
    - src.utils.gps_parser
    - src.models.course
"""

import sys
from pathlib import Path

# Add src directory to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.models.course import CourseProfile
from src.utils.gps_parser import GPSParser, GPSParserConfig


def main():
    """Main demo function showing GPS parser usage."""
    print("🚴 GPS Parser Demo")
    print("=" * 50)

    # Initialize GPS parser with default configuration
    config = GPSParserConfig()
    parser = GPSParser(config)

    # Path to example GPX files
    gpx_dir = current_dir / "gpx"

    # List of example GPX files to demonstrate
    example_files = [
        ("flat_course.gpx", "Flat Course"),
        ("hilly_course.gpx", "Hilly Course"),
        ("mountain_course.gpx", "Mountain Course"),
        ("urban_course.gpx", "Urban Course"),
        ("edge_cases.gpx", "Edge Cases"),
    ]

    print(f"Loading example GPX files from: {gpx_dir}")
    print()

    # Parse each example file and display results
    for filename, display_name in example_files:
        file_path = gpx_dir / filename

        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue

        print(f"📁 Processing: {display_name} ({filename})")
        print("-" * 40)

        try:
            # Parse the GPX file
            course_profile = parser.parse_gpx_file(str(file_path))

            # Display basic course information
            display_course_info(course_profile)

            # Display GPS metadata
            display_gps_metadata(course_profile.gps_metadata)

            # Display key climbs
            display_key_climbs(course_profile.key_climbs)

        except Exception as e:
            print(f"❌ Error parsing {filename}: {e}")

        print()
        print()


def display_course_info(course: CourseProfile):
    """Display basic course information."""
    print("📊 Course Overview:")
    print(f"   Name: {course.name}")
    print(f"   Distance: {course.bike_distance_miles:.1f} miles")
    print(f"   Elevation Gain: {course.bike_elevation_gain_ft:,} ft")
    print(f"   Base Altitude: {course.altitude_ft:,} ft")

    if course.start_coords:
        print(f"   Start: {course.start_coords[0]:.4f}, {course.start_coords[1]:.4f}")
    if course.finish_coords:
        print(
            f"   Finish: {course.finish_coords[0]:.4f}, {course.finish_coords[1]:.4f}"
        )

    # Calculate difficulty rating
    difficulty = calculate_difficulty_rating(course)
    print(f"   Difficulty: {difficulty}")


def display_gps_metadata(metadata):
    """Display GPS metadata information."""
    if not metadata:
        print("📡 GPS Metadata: Not available")
        return

    print("📡 GPS Data Quality:")
    print(f"   Total Points: {metadata.total_points:,}")
    print(f"   Quality Score: {metadata.data_quality_score:.1f}/100")

    if metadata.missing_elevation_points > 0:
        print(f"   Missing Elevation: {metadata.missing_elevation_points}")

    if metadata.total_validation_errors > 0:
        print(f"   Validation Errors: {metadata.total_validation_errors}")
        if metadata.invalid_latitude_points > 0:
            print(f"     - Invalid Latitude: {metadata.invalid_latitude_points}")
        if metadata.invalid_longitude_points > 0:
            print(f"     - Invalid Longitude: {metadata.invalid_longitude_points}")
        if metadata.invalid_elevation_points > 0:
            print(f"     - Invalid Elevation: {metadata.invalid_elevation_points}")
        if metadata.large_distance_jumps > 0:
            print(f"     - Large Distance Jumps: {metadata.large_distance_jumps}")

    if metadata.smoothed:
        print("   ✅ Data has been smoothed")


def display_key_climbs(climbs):
    """Display information about key climbs."""
    if not climbs:
        print("⛰️  Key Climbs: None detected")
        return

    print(f"⛰️  Key Climbs: {len(climbs)} detected")

    for i, climb in enumerate(climbs, 1):
        print(f"   {i}. {climb.name}")
        print(f"      Start: Mile {climb.start_mile:.1f}")
        print(f"      Length: {climb.length_miles:.1f} miles")
        print(f"      Elevation Gain: {climb.elevation_gain_ft:,} ft")
        print(f"      Average Grade: {climb.avg_grade:.1f}%")
        print(f"      Max Grade: {climb.max_grade:.1f}%")

        # Classify climb difficulty
        category = classify_climb_difficulty(climb)
        print(f"      Category: {category}")


def calculate_difficulty_rating(course: CourseProfile) -> str:
    """Calculate a simple difficulty rating for the course."""
    distance = course.bike_distance_miles
    elevation_gain = course.bike_elevation_gain_ft

    # Calculate elevation gain per mile
    elevation_per_mile = elevation_gain / distance if distance > 0 else 0

    # Simple rating system
    if elevation_per_mile < 50:
        return "🟢 Easy (Flat)"
    elif elevation_per_mile < 150:
        return "🟡 Moderate (Rolling)"
    elif elevation_per_mile < 300:
        return "🟠 Hard (Hilly)"
    elif elevation_per_mile < 500:
        return "🔴 Very Hard (Mountainous)"
    else:
        return "⚫ Extreme (Alpine)"


def classify_climb_difficulty(climb) -> str:
    """Classify climb difficulty based on length and grade."""
    avg_grade = climb.avg_grade

    # Simple classification system
    if avg_grade < 4:
        return "🟢 Easy"
    elif avg_grade < 6:
        return "🟡 Moderate"
    elif avg_grade < 8:
        return "🟠 Hard"
    elif avg_grade < 10:
        return "🔴 Very Hard"
    else:
        return "⚫ Extreme"


def demo_parser_configuration():
    """Demonstrate different parser configuration options."""
    print("🔧 Parser Configuration Examples")
    print("-" * 40)

    # Default configuration
    default_config = GPSParserConfig()
    print("Default Configuration:")
    print(
        f"   Climb detection threshold: {default_config.min_climb_length_miles} miles"
    )
    print(f"   Minimum grade for climb: {default_config.min_climb_grade}%")
    print(f"   Smoothing enabled: {default_config.enable_smoothing}")
    print()

    # Sensitive configuration (detects smaller climbs)
    sensitive_config = GPSParserConfig(
        min_climb_length_miles=0.1, min_climb_grade=2.0, enable_smoothing=True
    )
    print("Sensitive Configuration (detects more climbs):")
    print(
        f"   Climb detection threshold: {sensitive_config.min_climb_length_miles} miles"
    )
    print(f"   Minimum grade for climb: {sensitive_config.min_climb_grade}%")
    print()

    # Conservative configuration (only major climbs)
    conservative_config = GPSParserConfig(
        min_climb_length_miles=1.0, min_climb_grade=6.0, enable_smoothing=True
    )
    print("Conservative Configuration (only major climbs):")
    print(
        f"   Climb detection threshold: {conservative_config.min_climb_length_miles} miles"
    )
    print(f"   Minimum grade for climb: {conservative_config.min_climb_grade}%")


if __name__ == "__main__":
    main()
    print()
    demo_parser_configuration()

    print("\n" + "=" * 50)
    print("🎉 Demo complete!")
    print("\nFor more advanced usage, see:")
    print("  - examples/compare_courses.py")
    print("  - examples/climb_analysis.py")
    print("  - tests/test_gps_parser.py")
