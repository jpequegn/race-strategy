#!/usr/bin/env python3
"""
Course Comparison Demo Script

Compares multiple GPS courses side-by-side to analyze differences in difficulty,
climb profiles, and course characteristics.

Usage:
    python examples/compare_courses.py

Dependencies:
    - src.utils.gps_parser
    - src.models.course
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src directory to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.utils.gps_parser import GPSParser, GPSParserConfig
from src.models.course import CourseProfile


def main():
    """Main comparison function."""
    print("📊 GPS Course Comparison Tool")
    print("=" * 60)

    # Initialize GPS parser
    config = GPSParserConfig()
    parser = GPSParser(config)

    # Load all example courses
    courses = load_example_courses(parser)

    if not courses:
        print("❌ No courses loaded. Please check GPX files exist.")
        return

    # Perform various comparisons
    print_course_summary_table(courses)
    print()
    compare_difficulty_profiles(courses)
    print()
    compare_climb_statistics(courses)
    print()
    analyze_elevation_profiles(courses)
    print()
    compare_data_quality(courses)
    print()
    provide_course_recommendations(courses)


def load_example_courses(parser: GPSParser) -> List[Dict[str, Any]]:
    """Load all example GPX files and return course data."""
    gpx_dir = current_dir / "gpx"

    courses = []
    example_files = [
        ("flat_course.gpx", "Flat", "🟢"),
        ("hilly_course.gpx", "Hilly", "🟡"),
        ("mountain_course.gpx", "Mountain", "🔴"),
        ("urban_course.gpx", "Urban", "🏙️"),
        ("edge_cases.gpx", "Edge Cases", "⚠️"),
    ]

    print(f"Loading courses from: {gpx_dir}")

    for filename, name, emoji in example_files:
        file_path = gpx_dir / filename

        if not file_path.exists():
            print(f"⚠️  Skipping missing file: {filename}")
            continue

        try:
            course_profile = parser.parse_gpx_file(str(file_path))
            courses.append(
                {
                    "name": name,
                    "emoji": emoji,
                    "filename": filename,
                    "profile": course_profile,
                }
            )
            print(f"✅ Loaded: {name}")

        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")

    print(f"\nLoaded {len(courses)} courses for comparison\n")
    return courses


def print_course_summary_table(courses: List[Dict[str, Any]]):
    """Print a summary table comparing all courses."""
    print("📋 Course Summary Comparison")
    print("-" * 60)

    # Header
    print(
        f"{'Course':<15} {'Distance':<10} {'Elevation':<12} {'Climbs':<8} {'Rating':<15}"
    )
    print(f"{'='*15} {'='*10} {'='*12} {'='*8} {'='*15}")

    # Course data
    for course_data in courses:
        course = course_data["profile"]
        name = f"{course_data['emoji']} {course_data['name']}"
        distance = f"{course.bike_distance_miles:.1f} mi"
        elevation = f"{course.bike_elevation_gain_ft:,} ft"
        climbs = str(len(course.key_climbs))
        rating = calculate_difficulty_rating(course)

        print(f"{name:<15} {distance:<10} {elevation:<12} {climbs:<8} {rating:<15}")


def compare_difficulty_profiles(courses: List[Dict[str, Any]]):
    """Compare difficulty profiles across courses."""
    print("⚖️  Difficulty Profile Analysis")
    print("-" * 60)

    # Calculate various difficulty metrics
    metrics = []
    for course_data in courses:
        course = course_data["profile"]

        # Calculate metrics
        elevation_per_mile = (
            course.bike_elevation_gain_ft / course.bike_distance_miles
            if course.bike_distance_miles > 0
            else 0
        )
        steepest_climb = max(
            (climb.max_grade for climb in course.key_climbs), default=0
        )
        longest_climb = max(
            (climb.length_miles for climb in course.key_climbs), default=0
        )
        biggest_climb = max(
            (climb.elevation_gain_ft for climb in course.key_climbs), default=0
        )

        metrics.append(
            {
                "name": course_data["name"],
                "emoji": course_data["emoji"],
                "elevation_per_mile": elevation_per_mile,
                "steepest_climb": steepest_climb,
                "longest_climb": longest_climb,
                "biggest_climb": biggest_climb,
                "altitude": course.altitude_ft,
            }
        )

    # Print metrics
    print(
        f"{'Course':<15} {'Elev/Mile':<10} {'Steepest':<10} {'Longest':<10} {'Biggest':<10} {'Altitude':<10}"
    )
    print(f"{'='*15} {'='*10} {'='*10} {'='*10} {'='*10} {'='*10}")

    for m in metrics:
        name = f"{m['emoji']} {m['name']}"
        elev_per_mile = f"{m['elevation_per_mile']:.0f} ft/mi"
        steepest = f"{m['steepest_climb']:.1f}%" if m["steepest_climb"] > 0 else "None"
        longest = f"{m['longest_climb']:.1f} mi" if m["longest_climb"] > 0 else "None"
        biggest = f"{m['biggest_climb']:,} ft" if m["biggest_climb"] > 0 else "None"
        altitude = f"{m['altitude']:,} ft"

        print(
            f"{name:<15} {elev_per_mile:<10} {steepest:<10} {longest:<10} {biggest:<10} {altitude:<10}"
        )


def compare_climb_statistics(courses: List[Dict[str, Any]]):
    """Compare climbing statistics across courses."""
    print("🏔️  Climb Statistics Comparison")
    print("-" * 60)

    for course_data in courses:
        course = course_data["profile"]
        name = f"{course_data['emoji']} {course_data['name']}"

        print(f"{name}:")
        if not course.key_climbs:
            print("   No significant climbs detected")
        else:
            total_climb_distance = sum(
                climb.length_miles for climb in course.key_climbs
            )
            avg_climb_grade = sum(climb.avg_grade for climb in course.key_climbs) / len(
                course.key_climbs
            )

            print(f"   Total Climbs: {len(course.key_climbs)}")
            print(f"   Total Climb Distance: {total_climb_distance:.1f} miles")
            print(f"   Average Climb Grade: {avg_climb_grade:.1f}%")

            # Grade distribution
            grades = [climb.avg_grade for climb in course.key_climbs]
            easy_climbs = len([g for g in grades if g < 6])
            moderate_climbs = len([g for g in grades if 6 <= g < 10])
            hard_climbs = len([g for g in grades if g >= 10])

            if easy_climbs > 0:
                print(f"   Easy Climbs (<6%): {easy_climbs}")
            if moderate_climbs > 0:
                print(f"   Moderate Climbs (6-10%): {moderate_climbs}")
            if hard_climbs > 0:
                print(f"   Hard Climbs (>10%): {hard_climbs}")
        print()


def analyze_elevation_profiles(courses: List[Dict[str, Any]]):
    """Analyze elevation profile characteristics."""
    print("📈 Elevation Profile Analysis")
    print("-" * 60)

    for course_data in courses:
        course = course_data["profile"]
        name = f"{course_data['emoji']} {course_data['name']}"

        print(f"{name}:")

        if course.elevation_profile:
            # Analyze elevation data
            elevations = [point.elevation_ft for point in course.elevation_profile]
            min_elev = min(elevations)
            max_elev = max(elevations)
            elev_range = max_elev - min_elev

            print(
                f"   Elevation Range: {min_elev:,} ft to {max_elev:,} ft ({elev_range:,} ft)"
            )
            print(f"   Total GPS Points: {len(course.elevation_profile):,}")

            # Calculate grade distribution
            if len(course.elevation_profile) > 1:
                grades = []
                for i in range(1, len(course.elevation_profile)):
                    prev_point = course.elevation_profile[i - 1]
                    curr_point = course.elevation_profile[i]

                    # Calculate distance between points (simplified)
                    distance_miles = abs(
                        curr_point.distance_miles - prev_point.distance_miles
                    )
                    if distance_miles > 0:
                        elev_change = curr_point.elevation_ft - prev_point.elevation_ft
                        grade = (elev_change / (distance_miles * 5280)) * 100
                        grades.append(abs(grade))

                if grades:
                    avg_grade = sum(grades) / len(grades)
                    max_grade = max(grades)
                    steep_sections = len([g for g in grades if g > 8])

                    print(f"   Average Grade: {avg_grade:.1f}%")
                    print(f"   Maximum Grade: {max_grade:.1f}%")
                    print(f"   Steep Sections (>8%): {steep_sections}")
        else:
            print("   No elevation profile data available")

        print()


def compare_data_quality(courses: List[Dict[str, Any]]):
    """Compare GPS data quality across courses."""
    print("📊 GPS Data Quality Comparison")
    print("-" * 60)

    print(
        f"{'Course':<15} {'Points':<10} {'Quality':<10} {'Errors':<10} {'Missing':<10}"
    )
    print(f"{'='*15} {'='*10} {'='*10} {'='*10} {'='*10}")

    for course_data in courses:
        course = course_data["profile"]
        metadata = course.gps_metadata
        name = f"{course_data['emoji']} {course_data['name']}"

        if metadata:
            points = f"{metadata.total_points:,}"
            quality = f"{metadata.data_quality_score:.1f}/100"
            errors = str(metadata.total_validation_errors)
            missing = str(metadata.missing_elevation_points)
        else:
            points = "N/A"
            quality = "N/A"
            errors = "N/A"
            missing = "N/A"

        print(f"{name:<15} {points:<10} {quality:<10} {errors:<10} {missing:<10}")


def provide_course_recommendations(courses: List[Dict[str, Any]]):
    """Provide recommendations based on course analysis."""
    print("🎯 Course Recommendations")
    print("-" * 60)

    # Find courses with specific characteristics
    easiest_course = min(
        courses,
        key=lambda x: (
            x["profile"].bike_elevation_gain_ft / x["profile"].bike_distance_miles
            if x["profile"].bike_distance_miles > 0
            else float("inf")
        ),
    )
    hardest_course = max(
        courses,
        key=lambda x: x["profile"].bike_elevation_gain_ft
        / x["profile"].bike_distance_miles,
    )
    most_climbs = max(courses, key=lambda x: len(x["profile"].key_climbs))
    highest_altitude = max(courses, key=lambda x: x["profile"].altitude_ft)

    print("🥉 Beginner-Friendly Course:")
    print(
        f"   {easiest_course['emoji']} {easiest_course['name']} - Good for first-time triathletes"
    )
    print()

    print("🥇 Most Challenging Course:")
    print(
        f"   {hardest_course['emoji']} {hardest_course['name']} - For experienced athletes seeking a challenge"
    )
    print()

    print("🏔️  Best for Climb Training:")
    print(
        f"   {most_climbs['emoji']} {most_climbs['name']} - Most climbing opportunities ({len(most_climbs['profile'].key_climbs)} climbs)"
    )
    print()

    print("🏔️  High Altitude Training:")
    print(
        f"   {highest_altitude['emoji']} {highest_altitude['name']} - Altitude effects at {highest_altitude['profile'].altitude_ft:,} ft"
    )
    print()

    print("💡 Training Tips:")
    print("   • Start with flatter courses before progressing to hills")
    print("   • Practice climbing on courses with moderate grades first")
    print("   • Consider altitude acclimatization for high-elevation races")
    print("   • Urban courses help practice technical handling and pacing")


def calculate_difficulty_rating(course: CourseProfile) -> str:
    """Calculate difficulty rating for comparison."""
    distance = course.bike_distance_miles
    elevation_gain = course.bike_elevation_gain_ft

    elevation_per_mile = elevation_gain / distance if distance > 0 else 0

    if elevation_per_mile < 50:
        return "Easy"
    elif elevation_per_mile < 150:
        return "Moderate"
    elif elevation_per_mile < 300:
        return "Hard"
    elif elevation_per_mile < 500:
        return "Very Hard"
    else:
        return "Extreme"


if __name__ == "__main__":
    main()

    print("\n" + "=" * 60)
    print("🎉 Course comparison complete!")
    print("\nFor detailed climb analysis, run:")
    print("  python examples/climb_analysis.py")
