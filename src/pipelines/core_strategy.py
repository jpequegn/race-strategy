import dspy
from typing import Dict, Any, List
from ..models.course import CourseProfile
from ..models.athlete import AthleteProfile
from ..models.conditions import RaceConditions
from ..utils.course_analyzer import DifficultyCalculator
from .signatures import (
    EnhancedCourseAnalyzer,
    SegmentAnalyzer,
    AthleteAssessment,
    PacingStrategy,
    RiskAssessment,
    StrategyOptimizer,
)


class RaceStrategyPipeline:
    """Enhanced DSPy pipeline for race strategy generation with real GPS data and difficulty analysis"""

    def __init__(self):
        self.difficulty_calculator = DifficultyCalculator()
        self.enhanced_course_analyzer = dspy.ChainOfThought(EnhancedCourseAnalyzer)
        self.segment_analyzer = dspy.ChainOfThought(SegmentAnalyzer)
        self.athlete_assessor = dspy.ChainOfThought(AthleteAssessment)
        self.pacing_strategist = dspy.ChainOfThought(PacingStrategy)
        self.risk_assessor = dspy.ChainOfThought(RiskAssessment)
        self.strategy_optimizer = dspy.ChainOfThought(StrategyOptimizer)

    def generate_strategy(
        self, course: CourseProfile, athlete: AthleteProfile, conditions: RaceConditions
    ) -> Dict[str, Any]:
        """Execute the enhanced strategy generation pipeline with real GPS data and difficulty analysis"""

        # Step 1: Calculate objective course difficulty metrics
        difficulty_metrics = self.difficulty_calculator.calculate_difficulty(course)

        # Step 2: Enhanced course analysis with real GPS data and difficulty integration
        enhanced_course_analysis = self.enhanced_course_analyzer(
            course_name=course.name,
            course_profile=self._format_course_data(course),
            elevation_data=self._format_elevation_data(course),
            difficulty_metrics=self._format_difficulty_metrics(difficulty_metrics),
            crux_segments=self._format_crux_segments(difficulty_metrics.crux_segments),
        )

        # Step 3: Segment-by-segment analysis for major climbs/challenges
        segment_analyses = []
        for segment in difficulty_metrics.crux_segments[
            :5
        ]:  # Top 5 most critical segments
            segment_analysis = self.segment_analyzer(
                segment_data=self._format_segment_data(segment, course),
                segment_position=self._format_segment_position(segment, course),
                athlete_context=self._format_athlete_for_segment(athlete, segment),
            )
            segment_analyses.append(segment_analysis)

        # Step 4: Assess athlete vs enhanced course analysis
        athlete_assessment = self.athlete_assessor(
            athlete_profile=self._format_athlete_data(athlete),
            course_analysis=enhanced_course_analysis.strategic_analysis,
        )

        # Step 5: Generate pacing strategy with segment insights
        segment_insights = "\n".join(
            [
                f"Segment {i+1}: {sa.power_recommendation} | {sa.tactical_approach}"
                for i, sa in enumerate(segment_analyses)
            ]
        )

        pacing_strategy = self.pacing_strategist(
            athlete_assessment=f"Strengths: {athlete_assessment.strengths_vs_course}\n"
            f"Risks: {athlete_assessment.risk_areas}\n"
            f"Power: {athlete_assessment.power_targets}\n"
            f"Segment Insights: {segment_insights}",
            race_conditions=self._format_conditions_data(conditions),
        )

        # Step 6: Assess risks with enhanced analysis
        risk_assessment = self.risk_assessor(
            pacing_strategy=f"Swim: {pacing_strategy.swim_strategy}\n"
            f"Bike: {pacing_strategy.bike_strategy}\n"
            f"Run: {pacing_strategy.run_strategy}\n"
            f"Course Difficulty: {difficulty_metrics.overall_rating}/10\n"
            f"Key Challenges: {enhanced_course_analysis.tactical_insights}",
            race_conditions=self._format_conditions_data(conditions),
        )

        # Step 7: Optimize final strategy with all enhanced data
        final_strategy = self.strategy_optimizer(
            course_analysis=enhanced_course_analysis.strategic_analysis,
            athlete_assessment=athlete_assessment.strengths_vs_course,
            pacing_strategy=f"Swim: {pacing_strategy.swim_strategy}\n"
            f"Bike: {pacing_strategy.bike_strategy}\n"
            f"Run: {pacing_strategy.run_strategy}",
            risk_assessment=risk_assessment.mitigation_plan,
            target_time=athlete.target_finish_time or "Sub 6:00:00",
        )

        return {
            "difficulty_metrics": difficulty_metrics,
            "enhanced_course_analysis": enhanced_course_analysis,
            "segment_analyses": segment_analyses,
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

    def _format_elevation_data(self, course: CourseProfile) -> str:
        """Format detailed elevation profile for DSPy input"""
        elevation_profile = []

        # Create mile-by-mile elevation approximation from climb data
        total_miles = course.bike_distance_miles
        current_elevation = 0

        for mile in range(int(total_miles) + 1):
            mile_float = float(mile)
            gradient = 0

            # Find if this mile intersects with any climbs
            for climb in course.key_climbs:
                climb_start = climb.start_mile
                climb_end = climb.start_mile + climb.length_miles

                if climb_start <= mile_float <= climb_end:
                    # Calculate position within climb for gradient estimation
                    climb_position = (mile_float - climb_start) / climb.length_miles
                    if climb_position <= 1.0:
                        gradient = climb.avg_grade
                        break

            elevation_profile.append(f"Mile {mile}: {gradient:.1f}% gradient")

        return "\n".join(elevation_profile)

    def _format_difficulty_metrics(self, metrics) -> str:
        """Format difficulty calculator metrics for DSPy input"""
        return f"""
Overall Difficulty Rating: {metrics.overall_rating}/10
Elevation Intensity: {metrics.elevation_intensity:.1f} ft/mile
Average Gradient: {metrics.avg_gradient:.1f}%
Maximum Gradient: {metrics.max_gradient:.1f}%
Gradient Variance: {metrics.gradient_variance:.2f}
Climb Clustering Score: {metrics.climb_clustering_score:.2f} (0=rolling, 1=sustained)
Technical Difficulty: {metrics.technical_difficulty:.2f} (0-1 scale)

Difficulty Justification: {metrics.difficulty_justification}
"""

    def _format_crux_segments(self, crux_segments: List[Dict]) -> str:
        """Format crux segments for DSPy input"""
        if not crux_segments:
            return "No crux segments identified"

        segments_text = []
        for i, segment in enumerate(crux_segments, 1):
            segments_text.append(
                f"{i}. {segment['name']} (Mile {segment['start_mile']:.1f}): "
                f"{segment['length_miles']:.1f} miles at {segment['avg_grade']:.1f}% "
                f"(max {segment['max_grade']:.1f}%), {segment['elevation_gain_ft']}ft gain. "
                f"Difficulty Score: {segment['difficulty_score']:.2f}. "
                f"Strategic Importance: {segment['strategic_importance']}"
            )

        return "\n".join(segments_text)

    def _format_segment_data(self, segment: Dict, course: CourseProfile) -> str:
        """Format individual segment data for detailed analysis"""
        return f"""
Segment: {segment['name']}
Location: Mile {segment['start_mile']:.1f} - {segment['start_mile'] + segment['length_miles']:.1f}
Distance: {segment['length_miles']:.1f} miles
Average Gradient: {segment['avg_grade']:.1f}%
Maximum Gradient: {segment['max_grade']:.1f}%
Elevation Gain: {segment['elevation_gain_ft']} feet
Difficulty Score: {segment['difficulty_score']:.2f}
Strategic Importance: {segment['strategic_importance']}
"""

    def _format_segment_position(self, segment: Dict, course: CourseProfile) -> str:
        """Format segment position context within the race"""
        start_mile = segment["start_mile"]
        total_miles = course.bike_distance_miles
        position_pct = (start_mile / total_miles) * 100

        if position_pct < 25:
            race_phase = "Early race (first quarter)"
        elif position_pct < 50:
            race_phase = "Mid-race (second quarter)"
        elif position_pct < 75:
            race_phase = "Late-race (third quarter)"
        else:
            race_phase = "Final phase (last quarter)"

        return f"""
Race Position: {race_phase} ({position_pct:.0f}% through bike course)
Mile Position: {start_mile:.1f} of {total_miles} total bike miles
Fatigue Context: Athlete will have been racing for approximately {(start_mile / 16.0):.1f} hours at this point
Remaining Distance: {total_miles - start_mile - segment['length_miles']:.1f} miles after this segment
Run Impact: This segment occurs {13.1 if start_mile > total_miles * 0.9 else 'well'} before the run leg
"""

    def _format_athlete_for_segment(
        self, athlete: AthleteProfile, segment: Dict
    ) -> str:
        """Format athlete context relevant to a specific segment"""
        # Calculate approximate watts per kg if possible
        watts_per_kg = "Unknown"
        if athlete.ftp_watts and athlete.weight_lbs:
            weight_kg = athlete.weight_lbs * 0.453592
            watts_per_kg = f"{athlete.ftp_watts / weight_kg:.1f} W/kg"

        climbing_strength = "Unknown"
        if "climbing" in athlete.strengths or "bike" in athlete.strengths:
            climbing_strength = "Strong climber"
        elif "climbing" in athlete.limiters or "hills" in athlete.limiters:
            climbing_strength = "Climbing is a limiter"
        else:
            climbing_strength = "Average climbing ability"

        return f"""
Athlete: {athlete.name}
FTP: {athlete.ftp_watts}W ({watts_per_kg})
Climbing Ability: {climbing_strength}
Experience Level: {athlete.experience_level}
Relevant Strengths: {', '.join([s for s in athlete.strengths if s in ['bike', 'climbing', 'power']])}
Relevant Limiters: {', '.join([l for l in athlete.limiters if l in ['bike', 'climbing', 'hills', 'endurance']])}
Segment Challenge Level: {'High' if segment['difficulty_score'] > 0.7 else 'Moderate' if segment['difficulty_score'] > 0.4 else 'Manageable'}
"""
