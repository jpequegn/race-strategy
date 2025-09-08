import dspy


class EnhancedCourseAnalyzer(dspy.Signature):
    """Advanced course analysis using real GPS data and difficulty calculations"""

    # Course data inputs
    course_name: str = dspy.InputField(desc="Name of the race course")
    course_profile: str = dspy.InputField(
        desc="Detailed course profile with distances and elevation gains"
    )
    elevation_data: str = dspy.InputField(
        desc="Real GPS elevation profile with mile-by-mile gradients"
    )

    # Difficulty metrics from DifficultyCalculator
    difficulty_metrics: str = dspy.InputField(
        desc="Objective difficulty metrics: overall rating, elevation intensity, gradient stats"
    )
    crux_segments: str = dspy.InputField(
        desc="Most challenging segments identified by difficulty calculator"
    )

    # Strategic outputs
    strategic_analysis: str = dspy.OutputField(
        desc="Comprehensive strategic analysis based on real elevation data and difficulty metrics"
    )
    segment_analysis: str = dspy.OutputField(
        desc="Mile-by-mile strategic breakdown with specific power/effort recommendations"
    )
    power_pacing_plan: str = dspy.OutputField(
        desc="Detailed power targets and pacing strategy for each major segment"
    )
    tactical_insights: str = dspy.OutputField(
        desc="Race-winning tactical recommendations based on course characteristics"
    )
    difficulty_justification: str = dspy.OutputField(
        desc="Explanation of difficulty rating with specific challenges and opportunities"
    )


class SegmentAnalyzer(dspy.Signature):
    """Analyze individual course segments for detailed tactical recommendations"""

    segment_data: str = dspy.InputField(
        desc="Specific segment details: distance, elevation profile, gradient changes"
    )
    segment_position: str = dspy.InputField(
        desc="Segment position in race context (early/mid/late) and surrounding segments"
    )
    athlete_context: str = dspy.InputField(
        desc="Athlete's relevant capabilities and fatigue state at this point in race"
    )

    power_recommendation: str = dspy.OutputField(
        desc="Specific power target range and effort distribution for this segment"
    )
    tactical_approach: str = dspy.OutputField(
        desc="Optimal tactical approach: when to attack, recover, or maintain steady state"
    )
    risk_mitigation: str = dspy.OutputField(
        desc="Segment-specific risks and how to minimize them"
    )
    success_metrics: str = dspy.OutputField(
        desc="Key performance indicators to track success through this segment"
    )


class AthleteAssessment(dspy.Signature):
    """Assess athlete capabilities relative to course demands"""

    athlete_profile: str = dspy.InputField(
        desc="Athlete fitness metrics and experience"
    )
    course_analysis: str = dspy.InputField(desc="Course strategic analysis")
    strengths_vs_course: str = dspy.OutputField(
        desc="How athlete strengths align with course demands"
    )
    risk_areas: str = dspy.OutputField(
        desc="Potential problem areas based on athlete limiters"
    )
    power_targets: str = dspy.OutputField(
        desc="Recommended power zones for different course segments"
    )


class PacingStrategy(dspy.Signature):
    """Generate detailed pacing recommendations for each discipline"""

    athlete_assessment: str = dspy.InputField(
        desc="Athlete strengths and risk analysis"
    )
    race_conditions: str = dspy.InputField(desc="Weather and environmental factors")
    swim_strategy: str = dspy.OutputField(
        desc="Swim pacing and positioning recommendations"
    )
    bike_strategy: str = dspy.OutputField(
        desc="Detailed bike power/effort distribution by course segment"
    )
    run_strategy: str = dspy.OutputField(
        desc="Run pacing plan accounting for bike fatigue and course elevation"
    )


class RiskAssessment(dspy.Signature):
    """Identify and mitigate race day risks"""

    pacing_strategy: str = dspy.InputField(desc="Proposed race strategy")
    race_conditions: str = dspy.InputField(desc="Environmental conditions")
    primary_risks: str = dspy.OutputField(desc="Top 3 most likely race day risks")
    mitigation_plan: str = dspy.OutputField(
        desc="Specific actions to reduce identified risks"
    )
    contingency_options: str = dspy.OutputField(
        desc="Plan B strategies if things go wrong"
    )


class NutritionStrategy(dspy.Signature):
    """Generate comprehensive race nutrition plan based on physiology and conditions"""

    athlete_profile: str = dspy.InputField(
        desc="Weight, experience, nutrition preferences, and race history"
    )
    race_duration: str = dspy.InputField(
        desc="Predicted race time and effort distribution across disciplines"
    )
    conditions: str = dspy.InputField(
        desc="Temperature, humidity, race logistics and aid station availability"
    )
    nutrition_calculations: str = dspy.InputField(
        desc="Calculated sweat rate, carb needs, and sodium requirements per hour"
    )
    pacing_strategy: str = dspy.InputField(
        desc="Race pacing plan to optimize nutrition timing"
    )

    hydration_plan: str = dspy.OutputField(
        desc="Hour-by-hour fluid intake with specific amounts and products"
    )
    fueling_schedule: str = dspy.OutputField(
        desc="Carbohydrate and calorie timing throughout race with specific products"
    )
    electrolyte_strategy: str = dspy.OutputField(
        desc="Sodium and mineral replacement plan with timing and products"
    )
    contingency_nutrition: str = dspy.OutputField(
        desc="Backup plan if primary strategy fails, including GI distress protocol"
    )
    integration_guidance: str = dspy.OutputField(
        desc="How nutrition timing integrates with pacing and course demands"
    )


class EquipmentStrategy(dspy.Signature):
    """Optimize equipment selection for race conditions"""

    course_profile: str = dspy.InputField(
        desc="Elevation, technical sections, surface conditions, and distance"
    )
    race_conditions: str = dspy.InputField(
        desc="Weather, water temperature, wind, and race logistics"
    )
    athlete_profile: str = dspy.InputField(
        desc="Power, budget, experience level, and equipment preferences"
    )
    equipment_analysis: str = dspy.InputField(
        desc="Technical equipment recommendations from database analysis"
    )
    pacing_strategy: str = dspy.InputField(
        desc="Race pacing plan to optimize equipment choices"
    )

    bike_setup: str = dspy.OutputField(
        desc="Gearing, wheels, position recommendations with rationale"
    )
    swim_gear: str = dspy.OutputField(
        desc="Wetsuit, goggles, accessories with decision rationale"
    )
    run_equipment: str = dspy.OutputField(
        desc="Shoes, clothing, accessories with performance rationale"
    )
    performance_impact: str = dspy.OutputField(
        desc="Expected time savings, costs, and priority ranking of changes"
    )
    integration_guidance: str = dspy.OutputField(
        desc="How equipment choices integrate with pacing and race strategy"
    )


class StrategyOptimizer(dspy.Signature):
    """Synthesize all analysis into final race strategy with time predictions"""

    course_analysis: str = dspy.InputField()
    athlete_assessment: str = dspy.InputField()
    pacing_strategy: str = dspy.InputField()
    risk_assessment: str = dspy.InputField()
    nutrition_strategy: str = dspy.InputField(desc="Hydration and fueling plan")
    equipment_strategy: str = dspy.InputField(desc="Equipment recommendations and setup")
    target_time: str = dspy.InputField(desc="Athlete's target finish time")

    final_strategy: str = dspy.OutputField(desc="Complete race execution plan")
    time_prediction: str = dspy.OutputField(
        desc="Realistic time prediction with splits"
    )
    success_probability: str = dspy.OutputField(
        desc="Likelihood of achieving target time (percentage)"
    )
    key_success_factors: str = dspy.OutputField(
        desc="Top 3 things that must go right to hit target"
    )
