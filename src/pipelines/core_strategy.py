import dspy
from typing import Dict, Any
from ..models.course import CourseProfile
from ..models.athlete import AthleteProfile
from ..models.conditions import RaceConditions
from .signatures import (
    CourseAnalyzer,
    AthleteAssessment,
    PacingStrategy,
    RiskAssessment,
    StrategyOptimizer,
)


class RaceStrategyPipeline:
    """Main DSPy pipeline for race strategy generation"""

    def __init__(self):
        self.course_analyzer = dspy.ChainOfThought(CourseAnalyzer)
        self.athlete_assessor = dspy.ChainOfThought(AthleteAssessment)
        self.pacing_strategist = dspy.ChainOfThought(PacingStrategy)
        self.risk_assessor = dspy.ChainOfThought(RiskAssessment)
        self.strategy_optimizer = dspy.ChainOfThought(StrategyOptimizer)

    def generate_strategy(
        self, course: CourseProfile, athlete: AthleteProfile, conditions: RaceConditions
    ) -> Dict[str, Any]:
        """Execute the complete strategy generation pipeline"""

        # Step 1: Analyze course
        course_analysis = self.course_analyzer(
            course_profile=self._format_course_data(course)
        )

        # Step 2: Assess athlete vs course
        athlete_assessment = self.athlete_assessor(
            athlete_profile=self._format_athlete_data(athlete),
            course_analysis=course_analysis.analysis,
        )

        # Step 3: Generate pacing strategy
        pacing_strategy = self.pacing_strategist(
            athlete_assessment=f"Strengths: {athlete_assessment.strengths_vs_course}\n"
            f"Risks: {athlete_assessment.risk_areas}\n"
            f"Power: {athlete_assessment.power_targets}",
            race_conditions=self._format_conditions_data(conditions),
        )

        # Step 4: Assess risks
        risk_assessment = self.risk_assessor(
            pacing_strategy=f"Swim: {pacing_strategy.swim_strategy}\n"
            f"Bike: {pacing_strategy.bike_strategy}\n"
            f"Run: {pacing_strategy.run_strategy}",
            race_conditions=self._format_conditions_data(conditions),
        )

        # Step 5: Optimize final strategy
        final_strategy = self.strategy_optimizer(
            course_analysis=course_analysis.analysis,
            athlete_assessment=athlete_assessment.strengths_vs_course,
            pacing_strategy=f"Swim: {pacing_strategy.swim_strategy}\n"
            f"Bike: {pacing_strategy.bike_strategy}\n"
            f"Run: {pacing_strategy.run_strategy}",
            risk_assessment=risk_assessment.mitigation_plan,
            target_time=athlete.target_finish_time or "Sub 6:00:00",
        )

        return {
            "course_analysis": course_analysis,
            "athlete_assessment": athlete_assessment,
            "pacing_strategy": pacing_strategy,
            "risk_assessment": risk_assessment,
            "final_strategy": final_strategy,
        }

    def _format_course_data(self, course: CourseProfile) -> str:
        """Format course data for DSPy input"""
        climbs_text = "\n".join(
            [
                f"- {climb.name}: Mile {climb.start_mile}-{climb.start_mile + climb.length_miles}, "
                f"{climb.avg_grade}% avg grade (max {climb.max_grade}%)"
                for climb in course.key_climbs
            ]
        )

        return f"""
Course: {course.name}
Bike: {course.bike_distance_miles} miles, {course.bike_elevation_gain_ft}ft gain
Run: {course.run_distance_miles} miles, {course.run_elevation_gain_ft}ft gain
Swim: {course.swim_distance_miles} miles

Key Climbs:
{climbs_text}

Technical Sections: {', '.join(course.technical_sections)}
"""

    def _format_athlete_data(self, athlete: AthleteProfile) -> str:
        """Format athlete data for DSPy input"""
        return f"""
Athlete: {athlete.name}
Experience: {athlete.experience_level}
FTP: {athlete.ftp_watts}W
Swim Pace: {athlete.swim_pace_per_100m}s/100m
Run Threshold: {athlete.run_threshold_pace} min/mile
Previous 70.3: {athlete.previous_70_3_time or "None"}
Target Time: {athlete.target_finish_time or "Not specified"}
Strengths: {', '.join(athlete.strengths)}
Limiters: {', '.join(athlete.limiters)}
Age: {athlete.age}, Weight: {athlete.weight_lbs}lbs
"""

    def _format_conditions_data(self, conditions: RaceConditions) -> str:
        """Format race conditions for DSPy input"""
        return f"""
Temperature: {conditions.temperature_f}°F
Wind: {conditions.wind_speed_mph}mph {conditions.wind_direction}
Precipitation: {conditions.precipitation}
Humidity: {conditions.humidity_percent}%
Cloud Cover: {conditions.cloud_cover}
Water Temp: {conditions.water_temp_f}°F
"""
