#!/usr/bin/env python3
"""
Nutrition Planning Demo

Demonstrates the triathlon nutrition strategy module with real-world scenarios.
Shows how the system generates personalized hydration, fueling, and electrolyte
strategies based on athlete physiology and race conditions.

Usage:
    python examples/nutrition_planning_demo.py
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.athlete import AthleteProfile
from src.models.conditions import RaceConditions
from src.pipelines.core_strategy import RaceStrategyPipeline
from src.utils.course_loader import load_happy_valley_70_3_gps
from src.utils.nutrition_calculator import NutritionCalculator


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_section(title: str, content: str):
    """Print a formatted section"""
    print(f"\n🔸 {title}")
    print("-" * 40)
    print(content)


def demo_nutrition_calculator():
    """Demonstrate the NutritionCalculator utilities"""
    print_header("NUTRITION CALCULATOR DEMO")

    # Create test athlete and conditions
    athlete = AthleteProfile(
        name="Sarah Johnson",
        ftp_watts=220,
        swim_pace_per_100m=95.0,
        run_threshold_pace=8.0,
        experience_level="intermediate",
        previous_70_3_time="5:45:00",
        strengths=["swim", "bike"],
        limiters=["run", "heat"],
        target_finish_time="5:30:00",
        weight_lbs=145,
        height_inches=66,
        age=32,
    )

    hot_conditions = RaceConditions(
        temperature_f=88,
        wind_speed_mph=8,
        wind_direction="variable",
        precipitation="none",
        humidity_percent=75,
    )

    cool_conditions = RaceConditions(
        temperature_f=68,
        wind_speed_mph=12,
        wind_direction="tailwind",
        precipitation="none",
        humidity_percent=50,
    )

    calc = NutritionCalculator()

    print(
        f"Athlete: {athlete.name} ({athlete.weight_lbs} lbs, "
        f"{athlete.experience_level})"
    )
    print(f"Target Time: {athlete.target_finish_time}")

    # Compare hot vs cool conditions
    hot_sweat = calc.calculate_sweat_rate(athlete, hot_conditions)
    cool_sweat = calc.calculate_sweat_rate(athlete, cool_conditions)

    print_section(
        "SWEAT RATE CALCULATIONS",
        f"""
Hot Conditions (88°F, 75% humidity):
  Predicted Sweat Rate: {hot_sweat:.1f} oz/hour

Cool Conditions (68°F, 50% humidity):
  Predicted Sweat Rate: {cool_sweat:.1f} oz/hour

Difference: {hot_sweat - cool_sweat:.1f} oz/hour more in heat
""",
    )

    # Carbohydrate needs
    race_duration = 5.5  # hours
    moderate_carbs = calc.calculate_carb_needs(race_duration, "moderate")
    high_carbs = calc.calculate_carb_needs(race_duration, "high")

    print_section(
        "CARBOHYDRATE RECOMMENDATIONS",
        f"""
Race Duration: {race_duration} hours

Moderate Intensity: {moderate_carbs}g/hour
High Intensity: {high_carbs}g/hour

Total Carbs Needed: {moderate_carbs * race_duration:.0f}g - """
        f"""{high_carbs * race_duration:.0f}g
""",
    )

    # Sodium calculations
    hot_sodium = calc.calculate_sodium_needs(hot_sweat, hot_conditions, athlete)
    cool_sodium = calc.calculate_sodium_needs(cool_sweat, cool_conditions, athlete)

    print_section(
        "SODIUM REQUIREMENTS",
        f"""
Hot Conditions: {hot_sodium}mg/hour
Cool Conditions: {cool_sodium}mg/hour

Total Race Sodium:
  Hot: {hot_sodium * race_duration:.0f}mg
  Cool: {cool_sodium * race_duration:.0f}mg
""",
    )

    # Fluid replacement
    hot_fluid, hot_pct = calc.calculate_fluid_replacement(hot_sweat)
    cool_fluid, cool_pct = calc.calculate_fluid_replacement(cool_sweat)

    print_section(
        "FLUID REPLACEMENT STRATEGY",
        f"""
Hot Conditions:
  Target: {hot_fluid} oz/hour ({hot_pct:.0f}% of sweat loss)
  Race Total: {hot_fluid * race_duration:.0f} oz

Cool Conditions:
  Target: {cool_fluid} oz/hour ({cool_pct:.0f}% of sweat loss)
  Race Total: {cool_fluid * race_duration:.0f} oz
""",
    )

    # Hour-by-hour schedule
    hot_schedule = calc.generate_hourly_schedule(
        race_duration, moderate_carbs, hot_fluid, hot_sodium
    )

    print_section(
        "HOURLY NUTRITION SCHEDULE (Hot Day)",
        f"""
Hour | Carbs (g) | Fluids (oz) | Sodium (mg)
-----|-----------|-------------|-------------
  1  |    {hot_schedule["carbs"][0]:2d}     |     {hot_schedule["fluids"][0]:2d}      |     {hot_schedule["sodium"][0]:3d}
  2  |    {hot_schedule["carbs"][1]:2d}     |     {hot_schedule["fluids"][1]:2d}      |     {hot_schedule["sodium"][1]:3d}
  3  |    {hot_schedule["carbs"][2]:2d}     |     {hot_schedule["fluids"][2]:2d}      |     {hot_schedule["sodium"][2]:3d}
  4  |    {hot_schedule["carbs"][3]:2d}     |     {hot_schedule["fluids"][3]:2d}      |     {hot_schedule["sodium"][3]:3d}
  5  |    {hot_schedule["carbs"][4]:2d}     |     {hot_schedule["fluids"][4]:2d}      |     {hot_schedule["sodium"][4]:3d}
  6  |    {hot_schedule["carbs"][5]:2d}     |     {hot_schedule["fluids"][5]:2d}      |     {hot_schedule["sodium"][5]:3d}

Notes:
- Hour 1 is reduced due to race start nerves
- Hour 6 is partial hour based on {race_duration} total race time
- Maintain consistent intake hours 2-5 for best performance
""",
    )

    # Environmental risk assessment
    hot_risks = calc.assess_environmental_risk(hot_conditions)
    cool_risks = calc.assess_environmental_risk(cool_conditions)

    print_section(
        "ENVIRONMENTAL RISK ASSESSMENT",
        f"""
Hot Day Risks:
  Heat Risk: {hot_risks["heat"]}
  Humidity Risk: {hot_risks["humidity"]}

Cool Day Risks:
  Heat Risk: {cool_risks["heat"]}
  Humidity Risk: {cool_risks["humidity"]}
""",
    )


def demo_full_integration():
    """Demonstrate full nutrition integration with race strategy pipeline"""
    print_header("FULL PIPELINE INTEGRATION DEMO")

    # Load a real course
    try:
        course = load_happy_valley_70_3_gps()
        print(f"✅ Loaded course: {course.name}")
    except Exception as e:
        print(f"⚠️  Could not load GPS course, using basic profile: {e}")
        from src.models.course import CourseProfile

        course = CourseProfile(
            name="Demo Course 70.3",
            bike_distance_miles=56.0,
            bike_elevation_gain_ft=2500,
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=800,
            key_climbs=[],
            technical_sections=[],
            altitude_ft=1200,
        )

    # Create athlete profile
    athlete = AthleteProfile(
        name="Mike Rodriguez",
        ftp_watts=285,
        swim_pace_per_100m=88.0,
        run_threshold_pace=7.2,
        experience_level="advanced",
        previous_70_3_time="5:10:00",
        strengths=["bike", "run"],
        limiters=["swim"],
        target_finish_time="4:58:00",  # Aggressive sub-5 goal
        weight_lbs=172,
        height_inches=71,
        age=28,
    )

    # Hot race conditions
    conditions = RaceConditions(
        temperature_f=92,
        wind_speed_mph=6,
        wind_direction="headwind",
        precipitation="none",
        humidity_percent=68,
    )

    print(f"Athlete: {athlete.name}")
    print(f"Target Time: {athlete.target_finish_time}")
    print(
        f"Course: {course.name} ({course.bike_distance_miles} mi bike, +{course.bike_elevation_gain_ft}ft)"
    )
    print(
        f"Conditions: {conditions.temperature_f}°F, {conditions.humidity_percent}% humidity"
    )

    # Generate complete race strategy including nutrition
    print("\n🔄 Generating comprehensive race strategy with nutrition...")

    try:
        # Note: This requires DSPy to be configured with an LLM
        # For demo purposes, we'll show the nutrition calculations only
        pipeline = RaceStrategyPipeline()
        calc = pipeline.nutrition_calculator

        # Calculate nutrition requirements
        race_duration = 5.0  # Estimated from target time
        sweat_rate = calc.calculate_sweat_rate(athlete, conditions)
        carbs_per_hour = calc.calculate_carb_needs(
            race_duration, "high"
        )  # Aggressive pace
        sodium_per_hour = calc.calculate_sodium_needs(sweat_rate, conditions, athlete)
        fluid_per_hour, replacement_pct = calc.calculate_fluid_replacement(sweat_rate)

        schedule = calc.generate_hourly_schedule(
            race_duration, carbs_per_hour, fluid_per_hour, sodium_per_hour
        )

        env_risks = calc.assess_environmental_risk(conditions)

        print_section(
            "CALCULATED NUTRITION REQUIREMENTS",
            f"""
Race Duration: {race_duration:.1f} hours (sub-5:00 goal)
Sweat Rate: {sweat_rate:.1f} oz/hour (hot/humid conditions)
Fluid Target: {fluid_per_hour} oz/hour ({replacement_pct:.0f}% replacement)
Carbohydrate Target: {carbs_per_hour}g/hour (high intensity)
Sodium Target: {sodium_per_hour}mg/hour
""",
        )

        print_section(
            "RACE-SPECIFIC RECOMMENDATIONS",
            f"""
Environmental Challenges:
  {env_risks["heat"]}
  {env_risks["humidity"]}

Pacing Integration:
  • Pre-cool before race start (ice vest, cold fluids)
  • Start conservative on bike due to heat
  • Front-load nutrition early when feeling good
  • Monitor heat stress signs throughout

Course-Specific Notes:
  • {course.bike_elevation_gain_ft}ft climbing increases heat production
  • Higher carb needs due to aggressive {athlete.target_finish_time} goal
  • Aid station strategy critical for hot day execution
""",
        )

        print_section(
            "HOUR-BY-HOUR EXECUTION PLAN",
            f"""
Pre-Race (T-3 hours):
  • Large meal with familiar carbs (600-800 calories)
  • Begin hydration protocol (16-20 oz/hour)
  • Pre-cooling strategies if available

Swim (0-1 hours):
  • Minimal nutrition needs
  • Focus on positioning and effort control
  • Prepare for T1 nutrition start

Bike Hours 1-3:
  Hour 1: {schedule["carbs"][0]}g carbs, {schedule["fluids"][0]} oz fluid, {schedule["sodium"][0]}mg sodium
  Hour 2: {schedule["carbs"][1]}g carbs, {schedule["fluids"][1]} oz fluid, {schedule["sodium"][1]}mg sodium
  Hour 3: {schedule["carbs"][2]}g carbs, {schedule["fluids"][2]} oz fluid, {schedule["sodium"][2]}mg sodium

Run Hours 4-5:
  Hour 4: {schedule["carbs"][3]}g carbs, {schedule["fluids"][3]} oz fluid, {schedule["sodium"][3]}mg sodium
  Hour 5: {schedule["carbs"][4]}g carbs, {schedule["fluids"][4]} oz fluid (final hour to finish)

Hot Weather Adjustments:
  • Increase fluid intake by 10-15% if sweating heavily
  • Use ice in special needs bags
  • Pour water over head/neck for cooling
  • Be flexible with carb sources if GI issues develop
""",
        )

        print_section(
            "CONTINGENCY PLANS",
            """
IF Overheating:
  • Reduce pace 5-10%
  • Increase cooling strategies (ice, water)
  • Maintain electrolyte intake even if reducing carbs

IF GI Distress:
  • Switch to liquid nutrition only
  • Reduce carb concentration
  • Maintain fluid and sodium intake
  • Use aid station bananas/pretzels if needed

IF Cramping:
  • Increase sodium intake immediately
  • Check pacing - may be going too hard
  • Stretch and massage affected areas
  • Consider additional electrolyte sources
""",
        )

    except Exception as e:
        print(f"⚠️  Pipeline requires DSPy LLM configuration: {e}")
        print("   Showing nutrition calculations only for demo")


def main():
    """Run the nutrition planning demonstration"""
    print("🏊‍♀️🚴‍♀️🏃‍♀️ TRIATHLON NUTRITION STRATEGY DEMO 🏃‍♀️🚴‍♀️🏊‍♀️")
    print("This demo shows how the system generates personalized nutrition plans")
    print("based on athlete physiology, race conditions, and course demands.")

    # Demo 1: Basic nutrition calculator
    demo_nutrition_calculator()

    # Demo 2: Full integration with race strategy
    demo_full_integration()

    print_header("DEMO COMPLETE")
    print(
        """
This demonstration showed:
✅ Sweat rate calculations based on weight, temperature, and humidity
✅ Personalized carbohydrate recommendations by race duration and intensity
✅ Sodium requirements accounting for environmental conditions
✅ Hour-by-hour nutrition scheduling with practical adjustments
✅ Environmental risk assessment and adaptation strategies
✅ Integration with overall race strategy and pacing

The nutrition module provides evidence-based recommendations while
remaining flexible for individual preferences and race-day adjustments.

Key Features:
• Sports nutrition science compliance (30-90g carbs/hour guidelines)
• Environmental adaptation (heat/humidity impact on sweat rate)
• Personalized calculations (body weight, experience level)
• Practical scheduling (reduced first hour, flexible final hour)
• Safety limits (maximum sodium intake capped at 800mg/hour)
• Contingency planning (GI distress, overheating protocols)

For race day success, always practice your nutrition strategy during
training and have backup plans ready!
"""
    )


if __name__ == "__main__":
    main()
