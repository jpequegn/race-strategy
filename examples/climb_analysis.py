#!/usr/bin/env python3
"""
Detailed Climb Analysis Demo Script

Provides comprehensive analysis of climbing segments in GPS courses.
Includes climb categorization, power estimates, pacing strategies,
and training recommendations.

Usage:
    python examples/climb_analysis.py

Dependencies:
    - src.utils.gps_parser
    - src.models.course
"""

import math
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add src directory to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.models.course import ClimbSegment
from src.utils.gps_parser import GPSParser, GPSParserConfig


def main():
    """Main climb analysis function."""
    print("🏔️  Advanced Climb Analysis Tool")
    print("=" * 70)

    # Initialize GPS parser with sensitive settings to catch more climbs
    config = GPSParserConfig(
        min_climb_length_miles=0.1,  # Catch shorter climbs
        min_climb_grade=3.0,  # Lower grade threshold
        enable_smoothing=True,
    )
    parser = GPSParser(config)

    # Load courses with climbing focus
    courses = load_climbing_courses(parser)

    if not courses:
        print("❌ No courses loaded for climb analysis.")
        return

    # Perform detailed climb analysis
    all_climbs = collect_all_climbs(courses)

    if not all_climbs:
        print("📊 No significant climbs found in any course.")
        return

    print(f"Found {len(all_climbs)} climbs across {len(courses)} courses\n")

    # Various analysis sections
    analyze_climb_categories(all_climbs)
    print()
    analyze_climb_difficulty_scoring(all_climbs)
    print()
    analyze_power_requirements(all_climbs)
    print()
    analyze_pacing_strategies(all_climbs)
    print()
    compare_similar_climbs(all_climbs)
    print()
    provide_training_recommendations(all_climbs)
    print()
    generate_climb_profiles(courses)


def load_climbing_courses(parser: GPSParser) -> List[Dict[str, Any]]:
    """Load courses that have significant climbing."""
    gpx_dir = current_dir / "gpx"

    # Focus on courses with climbing potential
    climbing_courses = [
        ("hilly_course.gpx", "Hilly Course", "🟡"),
        ("mountain_course.gpx", "Mountain Course", "🔴"),
        ("urban_course.gpx", "Urban Course", "🏙️"),
    ]

    courses = []
    print("Loading courses with significant climbing...")

    for filename, name, emoji in climbing_courses:
        file_path = gpx_dir / filename

        if not file_path.exists():
            print(f"⚠️  Skipping missing file: {filename}")
            continue

        try:
            course_profile = parser.parse_gpx_file(str(file_path))
            if course_profile.key_climbs:  # Only include courses with climbs
                courses.append(
                    {
                        "name": name,
                        "emoji": emoji,
                        "filename": filename,
                        "profile": course_profile,
                    }
                )
                print(f"✅ Loaded: {name} ({len(course_profile.key_climbs)} climbs)")
            else:
                print(f"⚠️  No climbs found in: {name}")

        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")

    return courses


def collect_all_climbs(courses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collect all climbs from all courses with metadata."""
    all_climbs = []

    for course_data in courses:
        course = course_data["profile"]
        for climb in course.key_climbs:
            all_climbs.append(
                {
                    "climb": climb,
                    "course_name": course_data["name"],
                    "course_emoji": course_data["emoji"],
                }
            )

    return all_climbs


def analyze_climb_categories(climbs: List[Dict[str, Any]]):
    """Categorize climbs using cycling categorization system."""
    print("🏆 Climb Categorization (Cycling Standards)")
    print("-" * 70)

    categorized = []
    for climb_data in climbs:
        climb = climb_data["climb"]
        category = categorize_climb(climb)
        categorized.append(
            {
                "climb_data": climb_data,
                "category": category,
                "points": calculate_climb_points(climb),
            }
        )

    # Sort by difficulty (HC first, then Cat 1, etc.)
    category_order = ["HC", "1", "2", "3", "4", "Uncategorized"]
    categorized.sort(
        key=lambda x: (
            category_order.index(x["category"])
            if x["category"] in category_order
            else 999
        )
    )

    # Print categorized climbs
    for item in categorized:
        climb = item["climb_data"]["climb"]
        course = item["climb_data"]["course_name"]
        emoji = item["climb_data"]["course_emoji"]
        category = item["category"]
        points = item["points"]

        cat_emoji = get_category_emoji(category)
        print(f"{cat_emoji} Cat {category}: {climb.name}")
        print(f"    Course: {emoji} {course}")
        print(
            f"    Length: {climb.length_miles:.1f} mi | Grade: {climb.avg_grade:.1f}% | Gain: {climb.elevation_gain_ft:,} ft"
        )
        print(f"    Difficulty Points: {points:.0f}")
        print()


def analyze_climb_difficulty_scoring(climbs: List[Dict[str, Any]]):
    """Analyze climbs using various difficulty scoring systems."""
    print("📊 Climb Difficulty Scoring Systems")
    print("-" * 70)

    for climb_data in climbs:
        climb = climb_data["climb"]
        course = climb_data["course_name"]
        emoji = climb_data["course_emoji"]

        print(f"🏔️  {climb.name} ({emoji} {course})")

        # Multiple scoring systems
        fiets_score = calculate_fiets_score(climb)
        relative_difficulty = calculate_relative_difficulty(climb)
        vam_estimate = calculate_vam_estimate(climb)

        print(f"    FIETS Score: {fiets_score:.0f} (climbing difficulty index)")
        print(f"    Relative Difficulty: {relative_difficulty:.1f}/10")
        print(
            f"    Estimated VAM: {vam_estimate:.0f} m/h (Vertical Ascent Meters per hour)"
        )

        # Difficulty breakdown
        print("    Grade Analysis:")
        print(
            f"      - Average: {climb.avg_grade:.1f}% | Maximum: {climb.max_grade:.1f}%"
        )

        if climb.max_grade > climb.avg_grade * 1.5:
            print(
                f"      - ⚠️  Variable gradient (max {climb.max_grade:.1f}% vs avg {climb.avg_grade:.1f}%)"
            )

        print()


def analyze_power_requirements(climbs: List[Dict[str, Any]]):
    """Analyze estimated power requirements for each climb."""
    print("⚡ Estimated Power Requirements")
    print("-" * 70)
    print("Note: Estimates based on 70kg cyclist, moderate aerodynamics")
    print()

    for climb_data in climbs:
        climb = climb_data["climb"]
        course = climb_data["course_name"]
        emoji = climb_data["course_emoji"]

        print(f"🚴 {climb.name} ({emoji} {course})")

        # Power estimates for different pacing scenarios
        easy_power = estimate_climbing_power(climb, effort_level="easy")
        moderate_power = estimate_climbing_power(climb, effort_level="moderate")
        hard_power = estimate_climbing_power(climb, effort_level="hard")

        print("    Power Requirements (70kg cyclist):")
        print(
            f"      - Easy pace (recovery): {easy_power:.0f}W ({easy_power / 70:.1f} W/kg)"
        )
        print(
            f"      - Moderate pace (endurance): {moderate_power:.0f}W ({moderate_power / 70:.1f} W/kg)"
        )
        print(
            f"      - Hard pace (tempo): {hard_power:.0f}W ({hard_power / 70:.1f} W/kg)"
        )

        # Time estimates
        easy_time = estimate_climb_time(climb, effort_level="easy")
        moderate_time = estimate_climb_time(climb, effort_level="moderate")
        hard_time = estimate_climb_time(climb, effort_level="hard")

        print("    Estimated Climb Times:")
        print(f"      - Easy pace: {format_time(easy_time)}")
        print(f"      - Moderate pace: {format_time(moderate_time)}")
        print(f"      - Hard pace: {format_time(hard_time)}")

        print()


def analyze_pacing_strategies(climbs: List[Dict[str, Any]]):
    """Analyze optimal pacing strategies for each climb."""
    print("🎯 Pacing Strategy Recommendations")
    print("-" * 70)

    for climb_data in climbs:
        climb = climb_data["climb"]
        course = climb_data["course_name"]
        emoji = climb_data["course_emoji"]

        print(f"📈 {climb.name} ({emoji} {course})")

        # Analyze climb characteristics for pacing
        strategy = determine_pacing_strategy(climb)

        print(f"    Recommended Strategy: {strategy['name']}")
        print(f"    Rationale: {strategy['rationale']}")
        print("    Key Points:")
        for point in strategy["key_points"]:
            print(f"      • {point}")

        # Specific power zones
        print("    Power Zone Guidance:")
        print(
            f"      • First 1/3: {strategy['first_third']} ({strategy['first_third_power']})"
        )
        print(
            f"      • Middle 1/3: {strategy['middle_third']} ({strategy['middle_third_power']})"
        )
        print(
            f"      • Final 1/3: {strategy['final_third']} ({strategy['final_third_power']})"
        )

        print()


def compare_similar_climbs(climbs: List[Dict[str, Any]]):
    """Compare climbs with similar characteristics."""
    print("🔄 Similar Climb Comparisons")
    print("-" * 70)

    # Group climbs by similar characteristics
    short_steep = []
    long_moderate = []
    mixed_gradient = []

    for climb_data in climbs:
        climb = climb_data["climb"]

        if climb.length_miles < 1.0 and climb.avg_grade > 8:
            short_steep.append(climb_data)
        elif climb.length_miles > 2.0 and 4 <= climb.avg_grade <= 8:
            long_moderate.append(climb_data)
        elif climb.max_grade > climb.avg_grade * 1.4:
            mixed_gradient.append(climb_data)

    # Compare groups
    if short_steep:
        print("⚡ Short & Steep Climbs:")
        compare_climb_group(short_steep, "Power and anaerobic capacity")
        print()

    if long_moderate:
        print("🏃 Long & Moderate Climbs:")
        compare_climb_group(long_moderate, "Endurance and pacing")
        print()

    if mixed_gradient:
        print("🌊 Variable Gradient Climbs:")
        compare_climb_group(mixed_gradient, "Tactical pacing and gear selection")
        print()


def provide_training_recommendations(climbs: List[Dict[str, Any]]):
    """Provide specific training recommendations for each climb type."""
    print("🏋️  Training Recommendations")
    print("-" * 70)

    # Analyze climb distribution and provide targeted advice
    climb_types = analyze_climb_distribution(climbs)

    print("Based on your course climbs, focus training on:")
    print()

    if climb_types["short_steep"] > 0:
        print("💥 Short Steep Climbs Training:")
        print("   • VO2 Max intervals: 5x3min at 110-120% FTP")
        print("   • Neuromuscular power: 10x15sec all-out efforts")
        print("   • Standing climb practice with high cadence")
        print()

    if climb_types["long_moderate"] > 0:
        print("🔄 Long Moderate Climbs Training:")
        print("   • Tempo intervals: 3x20min at 85-95% FTP")
        print("   • Sweet spot training: 4x10min at 88-93% FTP")
        print("   • Seated climbing efficiency at target race power")
        print()

    if climb_types["variable"] > 0:
        print("🌊 Variable Gradient Training:")
        print("   • Over/under intervals: Alternate above/below FTP every 2min")
        print("   • Climbing technique: Practice shifting and position changes")
        print("   • Tactical pacing: Learn to read gradients and adjust effort")
        print()

    # Course-specific recommendations
    print("📋 Course-Specific Training Schedule:")
    for course_name, climbs_in_course in group_climbs_by_course(climbs).items():
        total_climbing = sum(c["climb"].elevation_gain_ft for c in climbs_in_course)
        longest_climb = max(c["climb"].length_miles for c in climbs_in_course)

        print(f"   {course_name}:")
        print(f"     • Total climbing volume: {total_climbing:,} ft")
        print(f"     • Longest single climb: {longest_climb:.1f} miles")
        print(f"     • Training focus: {get_training_focus(climbs_in_course)}")


def generate_climb_profiles(courses: List[Dict[str, Any]]):
    """Generate text-based elevation profiles for key climbs."""
    print("📈 Climb Elevation Profiles")
    print("-" * 70)

    for course_data in courses:
        course = course_data["profile"]
        if not course.key_climbs:
            continue

        print(f"{course_data['emoji']} {course_data['name']} - Key Climbs:")
        print()

        for i, climb in enumerate(
            course.key_climbs[:2], 1
        ):  # Show top 2 climbs per course
            print(f"  Climb {i}: {climb.name}")
            print(
                f"  Length: {climb.length_miles:.1f} mi | Grade: {climb.avg_grade:.1f}% avg, {climb.max_grade:.1f}% max"
            )

            # Generate simple text-based profile
            profile = generate_text_profile(climb)
            print(f"  Profile: {profile}")
            print()


# Helper functions


def categorize_climb(climb: ClimbSegment) -> str:
    """Categorize climb using cycling standards."""
    points = calculate_climb_points(climb)

    if points >= 1600:
        return "HC"  # Hors Catégorie
    elif points >= 800:
        return "1"
    elif points >= 400:
        return "2"
    elif points >= 200:
        return "3"
    elif points >= 100:
        return "4"
    else:
        return "Uncategorized"


def calculate_climb_points(climb: ClimbSegment) -> float:
    """Calculate climb difficulty points."""
    # Simplified FIETS-style calculation
    return (
        climb.elevation_gain_ft
        * (climb.avg_grade / 100)
        * math.sqrt(climb.length_miles)
    )


def get_category_emoji(category: str) -> str:
    """Get emoji for climb category."""
    emojis = {
        "HC": "🏆",
        "1": "🥇",
        "2": "🥈",
        "3": "🥉",
        "4": "🎯",
        "Uncategorized": "⚪",
    }
    return emojis.get(category, "⚪")


def calculate_fiets_score(climb: ClimbSegment) -> float:
    """Calculate FIETS difficulty score."""
    return (
        (climb.elevation_gain_ft / 3.281)
        * (climb.avg_grade / 100) ** 2
        * climb.length_miles
        * 1.609
    )


def calculate_relative_difficulty(climb: ClimbSegment) -> float:
    """Calculate relative difficulty on 1-10 scale."""
    # Normalize based on typical climb ranges
    base_score = (
        (climb.avg_grade / 20) * 5
        + (climb.length_miles / 10) * 3
        + (climb.elevation_gain_ft / 3000) * 2
    )
    return min(base_score, 10.0)


def calculate_vam_estimate(climb: ClimbSegment) -> float:
    """Calculate estimated VAM (Vertical Ascent Meters per hour)."""
    # Simplified estimate based on grade and length
    base_vam = 1200 - (climb.avg_grade - 6) * 50  # Decrease VAM with steeper grades
    return max(base_vam, 800)  # Minimum realistic VAM


def estimate_climbing_power(
    climb: ClimbSegment, effort_level: str = "moderate"
) -> float:
    """Estimate power required for climb (70kg cyclist)."""
    # Simplified power calculation
    base_power_per_grade = {"easy": 35, "moderate": 45, "hard": 55}  # Watts per % grade

    power_per_grade = base_power_per_grade.get(effort_level, 45)
    estimated_power = 150 + (
        climb.avg_grade * power_per_grade
    )  # Base power + gradient component

    return estimated_power


def estimate_climb_time(climb: ClimbSegment, effort_level: str = "moderate") -> float:
    """Estimate time to complete climb in minutes."""
    # Simplified speed calculation based on grade
    speed_mph = {
        "easy": 12 - climb.avg_grade * 0.4,
        "moderate": 15 - climb.avg_grade * 0.5,
        "hard": 18 - climb.avg_grade * 0.6,
    }

    speed = max(
        speed_mph.get(effort_level, 15 - climb.avg_grade * 0.5), 4.0
    )  # Minimum 4 mph
    time_hours = climb.length_miles / speed

    return time_hours * 60  # Convert to minutes


def determine_pacing_strategy(climb: ClimbSegment) -> Dict[str, Any]:
    """Determine optimal pacing strategy for a climb."""
    if climb.length_miles < 0.5:
        # Short climb - power strategy
        return {
            "name": "Power Strategy",
            "rationale": "Short climb allows for higher intensity throughout",
            "key_points": [
                "Start strong to establish rhythm",
                "Maintain high power output throughout",
                "Focus on technique over pacing",
            ],
            "first_third": "Strong start",
            "first_third_power": "105-110% target power",
            "middle_third": "Sustained effort",
            "middle_third_power": "100-105% target power",
            "final_third": "Finish strong",
            "final_third_power": "105-115% target power",
        }
    elif climb.length_miles > 3.0:
        # Long climb - conservation strategy
        return {
            "name": "Conservation Strategy",
            "rationale": "Long climb requires careful energy management",
            "key_points": [
                "Start conservatively to avoid early fatigue",
                "Maintain steady effort in middle section",
                "Save energy for final push if needed",
            ],
            "first_third": "Conservative start",
            "first_third_power": "90-95% target power",
            "middle_third": "Steady effort",
            "middle_third_power": "95-100% target power",
            "final_third": "Controlled finish",
            "final_third_power": "100-105% target power",
        }
    else:
        # Medium climb - balanced strategy
        return {
            "name": "Balanced Strategy",
            "rationale": "Medium length allows for steady effort with tactical adjustments",
            "key_points": [
                "Establish target pace early",
                "Adjust for gradient changes",
                "Finish at or slightly above target effort",
            ],
            "first_third": "Establish rhythm",
            "first_third_power": "95-100% target power",
            "middle_third": "Steady state",
            "middle_third_power": "100% target power",
            "final_third": "Strong finish",
            "final_third_power": "100-110% target power",
        }


def compare_climb_group(climb_group: List[Dict[str, Any]], focus_area: str):
    """Compare a group of similar climbs."""
    print(f"    Focus Area: {focus_area}")
    for climb_data in climb_group:
        climb = climb_data["climb"]
        course = climb_data["course_name"]
        emoji = climb_data["course_emoji"]

        difficulty = calculate_relative_difficulty(climb)
        print(f"    • {climb.name} ({emoji} {course})")
        print(
            f"      {climb.length_miles:.1f} mi, {climb.avg_grade:.1f}% avg, {climb.elevation_gain_ft:,} ft gain"
        )
        print(f"      Difficulty: {difficulty:.1f}/10")


def analyze_climb_distribution(climbs: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze distribution of climb types."""
    distribution = {"short_steep": 0, "long_moderate": 0, "variable": 0}

    for climb_data in climbs:
        climb = climb_data["climb"]

        if climb.length_miles < 1.0 and climb.avg_grade > 8:
            distribution["short_steep"] += 1
        elif climb.length_miles > 2.0 and 4 <= climb.avg_grade <= 8:
            distribution["long_moderate"] += 1
        elif climb.max_grade > climb.avg_grade * 1.4:
            distribution["variable"] += 1

    return distribution


def group_climbs_by_course(
    climbs: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Group climbs by their course."""
    grouped = {}
    for climb_data in climbs:
        course_name = climb_data["course_name"]
        if course_name not in grouped:
            grouped[course_name] = []
        grouped[course_name].append(climb_data)

    return grouped


def get_training_focus(climbs: List[Dict[str, Any]]) -> str:
    """Get training focus based on climb characteristics."""
    total_elevation = sum(c["climb"].elevation_gain_ft for c in climbs)
    avg_grade = sum(c["climb"].avg_grade for c in climbs) / len(climbs)

    if avg_grade > 8:
        return "Power and VO2 max development"
    elif total_elevation > 3000:
        return "Endurance and climbing volume"
    else:
        return "Tempo and threshold development"


def generate_text_profile(climb: ClimbSegment) -> str:
    """Generate a simple text-based elevation profile."""
    # Create a simple ASCII-style profile
    if climb.avg_grade < 4:
        return "▁▂▃▄▃▂▁ (gentle)"
    elif climb.avg_grade < 8:
        return "▂▄▆█▆▄▂ (moderate)"
    else:
        return "▄██████▄ (steep)"


def format_time(minutes: float) -> str:
    """Format time in minutes to hours:minutes format."""
    hours = int(minutes // 60)
    mins = int(minutes % 60)

    if hours > 0:
        return f"{hours}h {mins}m"
    else:
        return f"{mins}m"


if __name__ == "__main__":
    main()

    print("\n" + "=" * 70)
    print("🎉 Advanced climb analysis complete!")
    print("\nThis analysis helps you understand:")
    print("  • Climb difficulty using professional cycling standards")
    print("  • Power requirements and pacing strategies")
    print("  • Specific training recommendations for each climb type")
    print("  • Tactical approaches for race day success")
