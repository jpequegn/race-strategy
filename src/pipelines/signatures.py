import dspy

class CourseAnalyzer(dspy.Signature):
    """Analyze race course characteristics and identify key strategic points"""
    course_profile: str = dspy.InputField(desc="Detailed course elevation and technical data")
    analysis: str = dspy.OutputField(desc="Strategic analysis of course challenges and opportunities")
    key_segments: str = dspy.OutputField(desc="List of 3-5 most critical course segments for strategy")
    difficulty_rating: str = dspy.OutputField(desc="Overall difficulty rating (1-10) with justification")

class AthleteAssessment(dspy.Signature):
    """Assess athlete capabilities relative to course demands"""
    athlete_profile: str = dspy.InputField(desc="Athlete fitness metrics and experience")
    course_analysis: str = dspy.InputField(desc="Course strategic analysis")
    strengths_vs_course: str = dspy.OutputField(desc="How athlete strengths align with course demands")
    risk_areas: str = dspy.OutputField(desc="Potential problem areas based on athlete limiters")
    power_targets: str = dspy.OutputField(desc="Recommended power zones for different course segments")

class PacingStrategy(dspy.Signature):
    """Generate detailed pacing recommendations for each discipline"""
    athlete_assessment: str = dspy.InputField(desc="Athlete strengths and risk analysis")
    race_conditions: str = dspy.InputField(desc="Weather and environmental factors")
    swim_strategy: str = dspy.OutputField(desc="Swim pacing and positioning recommendations")
    bike_strategy: str = dspy.OutputField(desc="Detailed bike power/effort distribution by course segment")
    run_strategy: str = dspy.OutputField(desc="Run pacing plan accounting for bike fatigue and course elevation")

class RiskAssessment(dspy.Signature):
    """Identify and mitigate race day risks"""
    pacing_strategy: str = dspy.InputField(desc="Proposed race strategy")
    race_conditions: str = dspy.InputField(desc="Environmental conditions")
    primary_risks: str = dspy.OutputField(desc="Top 3 most likely race day risks")
    mitigation_plan: str = dspy.OutputField(desc="Specific actions to reduce identified risks")
    contingency_options: str = dspy.OutputField(desc="Plan B strategies if things go wrong")

class StrategyOptimizer(dspy.Signature):
    """Synthesize all analysis into final race strategy with time predictions"""
    course_analysis: str = dspy.InputField()
    athlete_assessment: str = dspy.InputField()
    pacing_strategy: str = dspy.InputField()
    risk_assessment: str = dspy.InputField()
    target_time: str = dspy.InputField(desc="Athlete's target finish time")
    
    final_strategy: str = dspy.OutputField(desc="Complete race execution plan")
    time_prediction: str = dspy.OutputField(desc="Realistic time prediction with splits")
    success_probability: str = dspy.OutputField(desc="Likelihood of achieving target time (percentage)")
    key_success_factors: str = dspy.OutputField(desc="Top 3 things that must go right to hit target")
