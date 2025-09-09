#!/usr/bin/env python3
"""
Equipment Selection System Demo

Demonstrates the triathlon equipment recommendation system with various
course and athlete scenarios. Shows bike setup, swim gear, and run equipment
recommendations based on course profile, conditions, and athlete capabilities.
"""

from src.models.athlete import AthleteProfile
from src.models.conditions import RaceConditions
from src.models.course import CourseProfile
from src.utils.equipment_database import EquipmentDatabase


def print_section_header(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}")


def print_subsection(title):
    """Print a formatted subsection"""
    print(f"\n{title}")
    print("-" * len(title))


def display_equipment_recommendations(db, course, athlete, conditions, scenario_name):
    """Display equipment recommendations for a given scenario"""

    print_section_header(f"EQUIPMENT RECOMMENDATIONS: {scenario_name}")

    # Course and conditions summary
    course_analysis = db.analyze_course_demands(course)
    print(f"Course: {course.name}")
    print(f"Bike Distance: {course.bike_distance_miles} miles")
    print(
        f"Bike Elevation: {course.bike_elevation_gain_ft} ft ({course_analysis['elevation_per_mile']} ft/mile)"
    )
    print(
        f"Course Type: {course_analysis['course_type']} ({course_analysis['climbing_demand']} climbing demand)"
    )
    print(
        f"Conditions: {conditions.temperature_f}°F, {conditions.wind_speed_mph} mph {conditions.wind_direction} wind"
    )
    print(
        f"Athlete: {athlete.name} ({athlete.experience_level}, {athlete.ftp_watts}W FTP)"
    )

    # Bike setup recommendations
    print_subsection("🚴 BIKE SETUP")
    gearing, gearing_rationale = db.recommend_bike_gearing(course, athlete, conditions)
    wheels, wheel_rationale = db.recommend_wheels(course, conditions)

    print(f"Gearing: {gearing.upper()}")
    print(f"Rationale: {gearing_rationale}")
    print()
    print(f"Wheels: {wheels.upper()}")
    print(f"Rationale: {wheel_rationale}")

    # Swim gear recommendations
    print_subsection("🏊 SWIM GEAR")
    wetsuit_decision, wetsuit_type, wetsuit_rationale = db.recommend_wetsuit_decision(
        conditions, athlete
    )

    print(f"Wetsuit Decision: {wetsuit_decision.upper()}")
    if wetsuit_decision == "wetsuit":
        print(f"Wetsuit Type: {wetsuit_type.upper()}")
    print(f"Rationale: {wetsuit_rationale}")

    # Run equipment recommendations
    print_subsection("👟 RUN EQUIPMENT")
    shoes, shoe_rationale = db.recommend_running_shoes(course, athlete)

    print(f"Shoes: {shoes.upper()}")
    print(f"Rationale: {shoe_rationale}")

    # Performance impact analysis
    print_subsection("⚡ PERFORMANCE IMPACT")
    equipment_changes = {
        "gearing": gearing,
        "wheels": wheels,
        "wetsuit_decision": wetsuit_decision,
        "shoes": shoes,
    }
    time_savings = db.estimate_time_savings(equipment_changes, course)
    print(f"Estimated Time Savings: {time_savings}")

    # Equipment priority ranking
    print_subsection("🎯 EQUIPMENT PRIORITIES")
    priorities = []

    if course_analysis["climbing_demand"] == "high" and gearing == "compact":
        priorities.append("1. Compact gearing (essential for climbing)")

    if wetsuit_decision == "wetsuit":
        priorities.append("2. Wetsuit (significant swim advantage)")

    if conditions.wind_speed_mph >= 25 and wheels == "all-around":
        priorities.append("3. All-around wheels (wind stability)")
    elif course_analysis["climbing_demand"] == "high" and wheels == "climbing":
        priorities.append("3. Climbing wheels (weight advantage)")
    elif wheels == "aero":
        priorities.append("3. Aero wheels (speed advantage)")

    if athlete.experience_level == "beginner" and shoes == "max-cushion":
        priorities.append("4. Max-cushion shoes (injury prevention)")

    if not priorities:
        priorities = ["Standard equipment setup appropriate for conditions"]

    for priority in priorities:
        print(priority)


def main():
    """Run equipment recommendation demos"""

    # Initialize equipment database
    db = EquipmentDatabase()

    # Scenario 1: Beginner athlete, hilly course, moderate conditions
    print_section_header("DEMO: TRIATHLON EQUIPMENT SELECTION SYSTEM")
    print("This demo showcases intelligent equipment recommendations")
    print("based on course profile, weather conditions, and athlete capabilities.")

    beginner_athlete = AthleteProfile(
        name="Sarah Johnson",
        ftp_watts=180,
        swim_pace_per_100m=95.0,
        run_threshold_pace=8.5,
        experience_level="beginner",
        previous_70_3_time=None,
        strengths=[],
        limiters=["swim", "run"],
        target_finish_time="6:30:00",
        weight_lbs=140,
        height_inches=66,
        age=28,
    )

    hilly_course = CourseProfile(
        name="Mountain Challenge 70.3",
        bike_distance_miles=56.0,
        bike_elevation_gain_ft=4200,  # ~75 ft/mile - mountainous
        swim_distance_miles=1.2,
        run_distance_miles=13.1,
        run_elevation_gain_ft=1400,
        key_climbs=["Mile 15-20: 6% grade", "Mile 35-40: 8% grade"],
        technical_sections=["Descent at mile 45"],
        altitude_ft=3000,
    )

    moderate_conditions = RaceConditions(
        temperature_f=68,
        wind_speed_mph=8,
        wind_direction="variable",
        precipitation="none",
        humidity_percent=55,
    )

    display_equipment_recommendations(
        db,
        hilly_course,
        beginner_athlete,
        moderate_conditions,
        "Beginner on Hilly Course",
    )

    # Scenario 2: Advanced athlete, flat course, windy conditions
    advanced_athlete = AthleteProfile(
        name="Mike Chen",
        ftp_watts=320,
        swim_pace_per_100m=78.0,
        run_threshold_pace=6.5,
        experience_level="advanced",
        previous_70_3_time="4:35:00",
        strengths=["bike", "run"],
        limiters=[],
        target_finish_time="4:25:00",
        weight_lbs=155,
        height_inches=71,
        age=32,
    )

    flat_course = CourseProfile(
        name="Speedway 70.3",
        bike_distance_miles=56.0,
        bike_elevation_gain_ft=800,  # ~14 ft/mile - flat
        swim_distance_miles=1.2,
        run_distance_miles=13.1,
        run_elevation_gain_ft=200,
        key_climbs=[],
        technical_sections=[],
        altitude_ft=50,
    )

    windy_conditions = RaceConditions(
        temperature_f=75,
        wind_speed_mph=28,
        wind_direction="crosswind",
        precipitation="none",
        humidity_percent=65,
    )

    display_equipment_recommendations(
        db,
        flat_course,
        advanced_athlete,
        windy_conditions,
        "Advanced Athlete in Windy Conditions",
    )

    # Scenario 3: Intermediate athlete, cold water, rolling course
    intermediate_athlete = AthleteProfile(
        name="Lisa Rodriguez",
        ftp_watts=240,
        swim_pace_per_100m=88.0,
        run_threshold_pace=7.8,
        experience_level="intermediate",
        previous_70_3_time="5:15:00",
        strengths=["swim"],
        limiters=["bike"],
        target_finish_time="5:05:00",
        weight_lbs=125,
        height_inches=64,
        age=35,
    )

    rolling_course = CourseProfile(
        name="Countryside Classic 70.3",
        bike_distance_miles=56.0,
        bike_elevation_gain_ft=2400,  # ~43 ft/mile - rolling
        swim_distance_miles=1.2,
        run_distance_miles=13.1,
        run_elevation_gain_ft=800,
        key_climbs=["Mile 10-12: 4% grade", "Mile 30-35: 5% grade"],
        technical_sections=[],
        altitude_ft=1200,
    )

    cold_conditions = RaceConditions(
        temperature_f=58,
        wind_speed_mph=12,
        wind_direction="headwind",
        precipitation="none",
        humidity_percent=70,
    )

    display_equipment_recommendations(
        db,
        rolling_course,
        intermediate_athlete,
        cold_conditions,
        "Cold Water Swimming Conditions",
    )

    # Summary
    print_section_header("EQUIPMENT SYSTEM SUMMARY")
    print("✅ Intelligent gearing recommendations based on course climbing demands")
    print("✅ Wind-aware wheel selection with safety prioritization")
    print(
        "✅ Temperature-based wetsuit decisions with athlete experience consideration"
    )
    print("✅ Experience-appropriate running shoe recommendations")
    print("✅ Performance impact analysis with time savings estimates")
    print("✅ Equipment priority ranking for optimal investment decisions")
    print("\nThe equipment system provides evidence-based recommendations that adapt")
    print(
        "to course characteristics, weather conditions, and individual athlete needs."
    )


if __name__ == "__main__":
    main()
