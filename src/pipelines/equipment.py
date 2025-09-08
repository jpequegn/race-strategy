"""
Equipment recommendation pipeline for triathlon race strategy.

Integrates equipment database analysis with DSPy AI reasoning to generate
comprehensive equipment recommendations based on course, conditions, and athlete profile.
"""

import dspy
from typing import Optional
from ..models.athlete import AthleteProfile
from ..models.conditions import RaceConditions
from ..models.course import CourseProfile
from ..models.equipment import (
    EquipmentRecommendations,
    BikeSetup,
    SwimGear,
    RunEquipment,
    AccessoryRecommendations,
    PerformanceImpact,
)
from ..utils.equipment_database import EquipmentDatabase
from .signatures import EquipmentStrategy


class EquipmentPipeline:
    """Equipment recommendation pipeline with DSPy integration"""

    def __init__(self):
        """Initialize equipment pipeline with database and DSPy components"""
        self.equipment_db = EquipmentDatabase()
        self.equipment_strategist = dspy.ChainOfThought(EquipmentStrategy)

    def generate_equipment_recommendations(
        self,
        course: CourseProfile,
        athlete: AthleteProfile,
        conditions: RaceConditions,
        pacing_strategy: Optional[str] = None,
    ) -> EquipmentRecommendations:
        """
        Generate comprehensive equipment recommendations.

        Args:
            course: Course profile with elevation and technical data
            athlete: Athlete capabilities and preferences
            conditions: Race day weather and environmental conditions
            pacing_strategy: Optional pacing strategy for integration

        Returns:
            Complete equipment recommendations with rationale
        """

        # Step 1: Technical equipment analysis using database
        technical_analysis = self._analyze_equipment_requirements(
            course, athlete, conditions
        )

        # Step 2: Generate AI-powered recommendations using DSPy
        ai_recommendations = self.equipment_strategist(
            course_profile=self._format_course_for_equipment(course),
            race_conditions=self._format_conditions_for_equipment(conditions),
            athlete_profile=self._format_athlete_for_equipment(athlete),
            equipment_analysis=technical_analysis,
            pacing_strategy=pacing_strategy or "Standard pacing approach",
        )

        # Step 3: Structure the recommendations
        return self._structure_equipment_recommendations(
            course, athlete, conditions, technical_analysis, ai_recommendations
        )

    def _analyze_equipment_requirements(
        self, course: CourseProfile, athlete: AthleteProfile, conditions: RaceConditions
    ) -> str:
        """Perform technical equipment analysis using database logic"""

        # Bike equipment analysis
        gearing, gearing_rationale = self.equipment_db.recommend_bike_gearing(
            course, athlete, conditions
        )
        wheels, wheel_rationale = self.equipment_db.recommend_wheels(course, conditions)

        # Swim equipment analysis
        wetsuit_decision, wetsuit_type, wetsuit_rationale = (
            self.equipment_db.recommend_wetsuit_decision(conditions, athlete)
        )

        # Run equipment analysis
        shoes, shoe_rationale = self.equipment_db.recommend_running_shoes(
            course, athlete
        )

        # Course demands analysis
        course_analysis = self.equipment_db.analyze_course_demands(course)

        # Performance impact analysis
        equipment_changes = {
            "gearing": gearing,
            "wheels": wheels,
            "wetsuit_decision": wetsuit_decision,
            "shoes": shoes,
        }
        time_savings = self.equipment_db.estimate_time_savings(
            equipment_changes, course
        )

        # Format technical analysis for DSPy
        technical_analysis = f"""
BIKE EQUIPMENT ANALYSIS:
Recommended Gearing: {gearing}
Rationale: {gearing_rationale}
Recommended Wheels: {wheels}
Rationale: {wheel_rationale}

SWIM EQUIPMENT ANALYSIS:
Wetsuit Decision: {wetsuit_decision}
Wetsuit Type: {wetsuit_type}
Rationale: {wetsuit_rationale}

RUN EQUIPMENT ANALYSIS:
Recommended Shoes: {shoes}
Rationale: {shoe_rationale}

COURSE DEMANDS:
Course Type: {course_analysis['course_type']}
Climbing Demand: {course_analysis['climbing_demand']}
Technical Level: {course_analysis['technical_level']}
Elevation per Mile: {course_analysis['elevation_per_mile']} ft/mile

PERFORMANCE IMPACT:
Estimated Time Savings: {time_savings}
Priority Equipment Changes: Wetsuit (if cold), Gearing (if hilly), Wheels (if flat/windy)
"""

        return technical_analysis

    def _format_course_for_equipment(self, course: CourseProfile) -> str:
        """Format course data for equipment analysis"""
        return f"""
Course: {course.name}
Bike Distance: {course.bike_distance_miles} miles
Bike Elevation: {course.bike_elevation_gain_ft} ft
Run Distance: {course.run_distance_miles} miles
Run Elevation: {course.run_elevation_gain_ft} ft
Swim Distance: {course.swim_distance_miles} miles
Technical Sections: {len(course.technical_sections) if course.technical_sections else 0}
Key Climbs: {len(course.key_climbs) if course.key_climbs else 0}
Altitude: {course.altitude_ft} ft
"""

    def _format_conditions_for_equipment(self, conditions: RaceConditions) -> str:
        """Format race conditions for equipment analysis"""
        return f"""
Temperature: {conditions.temperature_f}°F
Humidity: {conditions.humidity_percent}%
Wind Speed: {conditions.wind_speed_mph} mph
Wind Direction: {conditions.wind_direction}
Precipitation: {conditions.precipitation}
"""

    def _format_athlete_for_equipment(self, athlete: AthleteProfile) -> str:
        """Format athlete profile for equipment analysis"""
        return f"""
Athlete: {athlete.name}
Experience: {athlete.experience_level}
FTP: {athlete.ftp_watts} watts
Weight: {athlete.weight_lbs} lbs
Age: {athlete.age}
Strengths: {', '.join(athlete.strengths)}
Limiters: {', '.join(athlete.limiters)}
Target Time: {athlete.target_finish_time or 'Not specified'}
Previous 70.3 Time: {athlete.previous_70_3_time or 'Not specified'}
"""

    def _structure_equipment_recommendations(
        self,
        course: CourseProfile,
        athlete: AthleteProfile,
        conditions: RaceConditions,
        technical_analysis: str,
        ai_recommendations,
    ) -> EquipmentRecommendations:
        """Structure the final equipment recommendations"""

        # Extract technical recommendations for fallback
        gearing, _ = self.equipment_db.recommend_bike_gearing(course, athlete, conditions)
        wheels, _ = self.equipment_db.recommend_wheels(course, conditions)
        wetsuit_decision, wetsuit_type, _ = self.equipment_db.recommend_wetsuit_decision(
            conditions, athlete
        )
        shoes, _ = self.equipment_db.recommend_running_shoes(course, athlete)

        # Bike setup
        bike_setup = BikeSetup(
            gearing=gearing,
            gearing_rationale=ai_recommendations.bike_setup.split("Position:")[0].strip()
            if "Position:" in ai_recommendations.bike_setup
            else ai_recommendations.bike_setup[:200],
            wheels=wheels,
            wheel_rationale=f"Optimal for course conditions and {conditions.wind_speed_mph} mph wind",
            position="moderate",
            position_rationale="Balanced comfort and aerodynamics for triathlon racing",
            accessories=["GPS computer", "Nutrition storage", "Basic tools"],
        )

        # Swim gear
        swim_gear = SwimGear(
            wetsuit_decision=wetsuit_decision,
            wetsuit_rationale=ai_recommendations.swim_gear[:200],
            wetsuit_type=wetsuit_type if wetsuit_decision == "wetsuit" else None,
            goggles="clear" if conditions.precipitation == "none" else "tinted",
            goggle_rationale="Clear goggles for optimal visibility in race conditions",
            accessories=["Swim cap", "Anti-fog spray"],
        )

        # Run equipment
        run_equipment = RunEquipment(
            shoes=shoes,
            shoe_rationale=ai_recommendations.run_equipment[:200],
            clothing=self._recommend_run_clothing(conditions),
            clothing_rationale=f"Weather-appropriate for {conditions.temperature_f}°F conditions",
            accessories=["Race belt", "Hat/visor"],
            fuel_carrying="Gel flasks" if course.run_distance_miles > 10 else "Pockets",
        )

        # Accessories
        accessories = AccessoryRecommendations(
            nutrition_storage=["Bento box", "Frame bottles", "Rear hydration"],
            tools_spares=["CO2 cartridges", "Tire levers", "Spare tube", "Multi-tool"],
            electronics=["GPS watch", "Power meter (if available)"],
            other_gear=["Sunglasses", "Sunscreen", "Body marking pens"],
        )

        # Performance impact
        equipment_changes = {
            "gearing": gearing,
            "wheels": wheels,
            "wetsuit_decision": wetsuit_decision,
        }
        time_savings = self.equipment_db.estimate_time_savings(equipment_changes, course)

        performance_impact = PerformanceImpact(
            time_savings_estimate=time_savings,
            cost_analysis=ai_recommendations.performance_impact[:300]
            if hasattr(ai_recommendations, "performance_impact")
            else "Cost varies by specific equipment choices",
            priority_ranking=[
                "Proper gearing for course",
                "Appropriate wheels",
                "Wetsuit decision",
                "Comfortable shoes",
            ],
            risk_assessment="Low risk with proper equipment selection and familiarity",
            alternatives="Multiple options available in each category",
        )

        return EquipmentRecommendations(
            race_name=course.name,
            athlete_name=athlete.name,
            conditions_summary=f"{conditions.temperature_f}°F, {conditions.wind_speed_mph}mph wind",
            bike_setup=bike_setup,
            swim_gear=swim_gear,
            run_equipment=run_equipment,
            accessories=accessories,
            performance_impact=performance_impact,
            confidence_level="high",
            notes="Recommendations based on course analysis and race conditions",
        )

    def _recommend_run_clothing(self, conditions: RaceConditions) -> str:
        """Recommend run clothing based on weather conditions"""

        if conditions.temperature_f >= 75:
            return "Minimal clothing - shorts, singlet, lightweight fabrics"
        elif conditions.temperature_f >= 60:
            return "Light clothing - shorts, short sleeve, breathable materials"
        elif conditions.temperature_f >= 45:
            return "Moderate layers - tights/shorts, long sleeve, wind protection"
        else:
            return "Warm layers - tights, long sleeve, gloves, thermal protection"