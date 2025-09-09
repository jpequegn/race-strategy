"""
Equipment database and recommendation utilities.

Provides equipment catalog, decision matrices, and cost-benefit analysis
for triathlon equipment selection based on course, conditions, and athlete profile.
"""

from typing import Dict, List, Tuple
import math
from ..models.athlete import AthleteProfile
from ..models.conditions import RaceConditions
from ..models.course import CourseProfile


class EquipmentDatabase:
    """Equipment catalog and recommendation engine"""

    def __init__(self):
        """Initialize equipment database with catalog and decision matrices"""
        self.bike_gearing_matrix = {
            "flat_course": {"compact": 0.7, "standard": 0.9, "1x": 0.6},
            "rolling_course": {"compact": 0.8, "standard": 0.7, "1x": 0.7},
            "mountainous": {"compact": 1.0, "standard": 0.4, "1x": 0.7},
        }

        self.wheel_matrix = {
            "flat_windy": {"aero": 0.9, "climbing": 0.3, "all-around": 0.7},
            "hilly_calm": {"aero": 0.6, "climbing": 0.9, "all-around": 0.8},
            "hilly_windy": {"aero": 0.4, "climbing": 0.8, "all-around": 0.9},
            "mixed_conditions": {"aero": 0.7, "climbing": 0.7, "all-around": 0.9},
        }

        self.wetsuit_temperature_thresholds = {
            "definitely_wetsuit": 65,  # Below this, definitely wear wetsuit
            "probably_wetsuit": 70,  # 65-70F, probably wear wetsuit
            "athlete_choice": 75,  # 70-75F, athlete dependent
            "probably_no_wetsuit": 80,  # 75-80F, probably no wetsuit
            # Above 80F, definitely no wetsuit
        }

    def analyze_course_demands(self, course: CourseProfile) -> Dict[str, str]:
        """Analyze course characteristics to determine equipment needs"""

        # Calculate elevation intensity
        if hasattr(course, "bike_distance_miles") and course.bike_distance_miles > 0:
            elevation_per_mile = (
                course.bike_elevation_gain_ft / course.bike_distance_miles
            )
        else:
            elevation_per_mile = 0

        # Classify course type
        if elevation_per_mile < 30:
            course_type = "flat_course"
            climbing_demand = "low"
        elif elevation_per_mile < 60:
            course_type = "rolling_course"
            climbing_demand = "moderate"
        else:
            course_type = "mountainous"
            climbing_demand = "high"

        # Technical difficulty
        technical_level = "moderate"
        if hasattr(course, "technical_sections") and course.technical_sections:
            technical_level = "high"

        return {
            "course_type": course_type,
            "climbing_demand": climbing_demand,
            "technical_level": technical_level,
            "elevation_per_mile": f"{elevation_per_mile:.1f}",
        }

    def recommend_bike_gearing(
        self, course: CourseProfile, athlete: AthleteProfile, conditions: RaceConditions
    ) -> Tuple[str, str]:
        """Recommend optimal bike gearing based on course and athlete"""

        course_analysis = self.analyze_course_demands(course)
        course_type = course_analysis["course_type"]

        # Get gearing scores
        gearing_scores = self.bike_gearing_matrix.get(
            course_type, self.bike_gearing_matrix["rolling_course"]
        )

        # Athlete adjustments
        if athlete.experience_level == "beginner":
            gearing_scores["compact"] += 0.2  # Beginners benefit from easier gearing

        if athlete.ftp_watts > 300:  # Strong cyclists can handle standard gearing
            gearing_scores["standard"] += 0.1

        # Select best option
        best_gearing = max(gearing_scores.items(), key=lambda x: x[1])

        # Generate rationale
        rationale = self._generate_gearing_rationale(
            best_gearing[0], course_analysis, athlete
        )

        return best_gearing[0], rationale

    def recommend_wheels(
        self, course: CourseProfile, conditions: RaceConditions
    ) -> Tuple[str, str]:
        """Recommend optimal wheel choice based on course and conditions"""

        course_analysis = self.analyze_course_demands(course)

        # Determine conditions category
        if course_analysis["climbing_demand"] == "high":
            if conditions.wind_speed_mph > 15:
                condition_key = "hilly_windy"
            else:
                condition_key = "hilly_calm"
        elif conditions.wind_speed_mph > 15:  # Changed threshold for windy conditions
            condition_key = "flat_windy"
        else:
            condition_key = "mixed_conditions"

        # Get wheel scores (use mixed_conditions if key not found)
        wheel_scores = self.wheel_matrix.get(
            condition_key, self.wheel_matrix["mixed_conditions"]
        )

        # Wind adjustments
        if conditions.wind_speed_mph >= 25:
            wheel_scores[
                "aero"
            ] -= 0.3  # Strong crosswinds make aero wheels harder to handle

        best_wheels = max(wheel_scores.items(), key=lambda x: x[1])

        rationale = self._generate_wheel_rationale(
            best_wheels[0], course_analysis, conditions
        )

        return best_wheels[0], rationale

    def recommend_wetsuit_decision(
        self, conditions: RaceConditions, athlete: AthleteProfile
    ) -> Tuple[str, str, str]:
        """Recommend wetsuit decision based on water temperature and athlete"""

        # Assume water temp is close to air temp if not specified
        # In reality, this would come from race-specific data
        estimated_water_temp = conditions.temperature_f - 10  # Rough estimate

        decision = "depends-on-temp"
        wetsuit_type = None

        if (
            estimated_water_temp
            <= self.wetsuit_temperature_thresholds["definitely_wetsuit"]
        ):
            decision = "wetsuit"
            wetsuit_type = "full"
        elif (
            estimated_water_temp
            <= self.wetsuit_temperature_thresholds["probably_wetsuit"]
        ):
            decision = "wetsuit"
            wetsuit_type = (
                "full" if athlete.experience_level == "beginner" else "sleeveless"
            )
        elif (
            estimated_water_temp
            <= self.wetsuit_temperature_thresholds["athlete_choice"]
        ):
            if athlete.experience_level == "beginner" or "swim" in athlete.limiters:
                decision = "wetsuit"
                wetsuit_type = "sleeveless"
            else:
                decision = "no-wetsuit"
        elif (
            estimated_water_temp
            <= self.wetsuit_temperature_thresholds["probably_no_wetsuit"]
        ):
            decision = "no-wetsuit"
        else:
            decision = "no-wetsuit"

        rationale = self._generate_wetsuit_rationale(
            decision, estimated_water_temp, athlete
        )

        return decision, wetsuit_type or "none", rationale

    def recommend_running_shoes(
        self, course: CourseProfile, athlete: AthleteProfile
    ) -> Tuple[str, str]:
        """Recommend running shoe category based on course and athlete needs"""

        course_analysis = self.analyze_course_demands(course)

        # Base recommendation on athlete experience and course
        if athlete.experience_level == "beginner" or "run" in athlete.limiters:
            shoe_type = "max-cushion"
        elif course_analysis["climbing_demand"] == "high":
            shoe_type = "stability"  # More support for hills
        elif (
            athlete.experience_level == "advanced"
            and course_analysis["course_type"] == "flat_course"
        ):
            shoe_type = "neutral"  # Fast, responsive for experienced on flat
        else:
            shoe_type = "neutral"  # Default choice

        rationale = self._generate_shoe_rationale(shoe_type, course_analysis, athlete)

        return shoe_type, rationale

    def estimate_time_savings(
        self, equipment_changes: Dict[str, str], course: CourseProfile
    ) -> str:
        """Estimate time savings from equipment recommendations"""

        total_seconds_saved = 0

        # Aero wheels on flat course
        if equipment_changes.get("wheels") == "aero":
            if hasattr(course, "bike_distance_miles"):
                # Rough estimate: 30-60 seconds per hour for aero wheels
                bike_hours = course.bike_distance_miles / 20  # Assume ~20mph average
                total_seconds_saved += bike_hours * 45

        # Optimal gearing
        if equipment_changes.get("gearing") == "compact":
            course_analysis = self.analyze_course_demands(course)
            if course_analysis["climbing_demand"] == "high":
                total_seconds_saved += 120  # 2 minutes for proper gearing on hills

        # Wetsuit
        if equipment_changes.get("wetsuit_decision") == "wetsuit":
            total_seconds_saved += 90  # ~1.5 minutes for wetsuit buoyancy

        if total_seconds_saved < 60:
            return f"~{total_seconds_saved:.0f} seconds"
        else:
            minutes = total_seconds_saved / 60
            return f"~{minutes:.1f} minutes"

    def _generate_gearing_rationale(
        self, gearing: str, course_analysis: Dict, athlete: AthleteProfile
    ) -> str:
        """Generate explanation for gearing recommendation"""

        rationales = {
            "compact": f"Compact gearing recommended for {course_analysis['climbing_demand']} climbing demands",
            "standard": "Standard gearing suitable for flat course and strong cyclist",
            "1x": "Single chainring setup for simplicity and adequate range",
        }

        base_rationale = rationales.get(gearing, "Optimal gearing for course demands")

        if athlete.experience_level == "beginner" and gearing == "compact":
            base_rationale += (
                ". Easier gearing helps beginner maintain cadence on climbs."
            )

        return base_rationale

    def _generate_wheel_rationale(
        self, wheels: str, course_analysis: Dict, conditions: RaceConditions
    ) -> str:
        """Generate explanation for wheel recommendation"""

        rationales = {
            "aero": f"Aero wheels optimal for flat course with manageable wind ({conditions.wind_speed_mph} mph)",
            "climbing": f"Lightweight climbing wheels best for {course_analysis['climbing_demand']} elevation gain",
            "all-around": "Versatile all-around wheels balance aero and climbing performance",
        }

        base_rationale = rationales.get(wheels, "Optimal wheels for course conditions")

        # Add wind context for all-around wheels in windy conditions
        if wheels == "all-around" and conditions.wind_speed_mph >= 25:
            base_rationale += (
                f" - safer choice in strong {conditions.wind_speed_mph} mph wind"
            )
        elif wheels == "all-around" and conditions.wind_speed_mph > 15:
            base_rationale += f" for {conditions.wind_speed_mph} mph wind conditions"

        return base_rationale

    def _generate_wetsuit_rationale(
        self, decision: str, water_temp: float, athlete: AthleteProfile
    ) -> str:
        """Generate explanation for wetsuit recommendation"""

        if decision == "wetsuit":
            rationale = f"Wetsuit recommended for ~{water_temp:.0f}°F water temperature"
            if athlete.experience_level == "beginner":
                rationale += ". Provides buoyancy and confidence for newer swimmer."
        elif decision == "no-wetsuit":
            rationale = f"No wetsuit recommended for warmer ~{water_temp:.0f}°F water"
        else:
            rationale = f"Wetsuit optional at ~{water_temp:.0f}°F - athlete choice based on comfort"

        return rationale

    def _generate_shoe_rationale(
        self, shoe_type: str, course_analysis: Dict, athlete: AthleteProfile
    ) -> str:
        """Generate explanation for running shoe recommendation"""

        rationales = {
            "max-cushion": "Maximum cushioning for comfort and injury prevention",
            "stability": f"Stability features helpful for {course_analysis['climbing_demand']} climbing demands",
            "neutral": "Neutral shoes for efficient, responsive running",
            "minimal": "Minimal shoes for experienced runner seeking ground feel",
        }

        base_rationale = rationales.get(
            shoe_type, "Appropriate shoes for athlete and course"
        )

        if "run" in athlete.limiters:
            base_rationale += ". Extra support addresses running limiter."

        return base_rationale
