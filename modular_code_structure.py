# src/models/course.py
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ClimbSegment:
    """Individual climb within a course"""
    name: str
    start_mile: float
    length_miles: float
    avg_grade: float
    max_grade: float
    elevation_gain_ft: int

@dataclass
class CourseProfile:
    """Complete race course profile"""
    name: str
    bike_distance_miles: float
    bike_elevation_gain_ft: int
    swim_distance_miles: float
    run_distance_miles: float
    run_elevation_gain_ft: int
    key_climbs: List[ClimbSegment]
    technical_sections: List[str]
    surface_types: List[str] = None
    altitude_ft: int = 0

# ====================
# src/models/athlete.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class AthleteProfile:
    """Individual athlete capabilities and goals"""
    name: str
    ftp_watts: int
    swim_pace_per_100m: float  # seconds
    run_threshold_pace: float  # minutes per mile
    experience_level: str  # "beginner", "intermediate", "advanced"
    previous_70_3_time: Optional[str]  # "HH:MM:SS"
    strengths: List[str]  # ["swim", "bike", "run"]
    limiters: List[str]
    target_finish_time: Optional[str]
    weight_lbs: float = 150
    height_inches: float = 70
    age: int = 35

# ====================
# src/models/conditions.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class RaceConditions:
    """Environmental conditions for race day"""
    temperature_f: int
    wind_speed_mph: int
    wind_direction: str  # "headwind", "tailwind", "crosswind", "variable"
    precipitation: str  # "none", "light", "moderate", "heavy"
    humidity_percent: int
    cloud_cover: str = "mixed"  # "clear", "partial", "overcast"
    water_temp_f: Optional[int] = None

# ====================
# src/pipelines/signatures.py
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

# ====================
# src/pipelines/core_strategy.py
import dspy
from typing import Dict, Any
from ..models.course import CourseProfile
from ..models.athlete import AthleteProfile
from ..models.conditions import RaceConditions
from .signatures import (
    CourseAnalyzer, AthleteAssessment, PacingStrategy, 
    RiskAssessment, StrategyOptimizer
)

class RaceStrategyPipeline:
    """Main DSPy pipeline for race strategy generation"""
    
    def __init__(self):
        self.course_analyzer = dspy.ChainOfThought(CourseAnalyzer)
        self.athlete_assessor = dspy.ChainOfThought(AthleteAssessment)
        self.pacing_strategist = dspy.ChainOfThought(PacingStrategy)
        self.risk_assessor = dspy.ChainOfThought(RiskAssessment)
        self.strategy_optimizer = dspy.ChainOfThought(StrategyOptimizer)
    
    def generate_strategy(self, course: CourseProfile, athlete: AthleteProfile, 
                         conditions: RaceConditions) -> Dict[str, Any]:
        """Execute the complete strategy generation pipeline"""
        
        # Step 1: Analyze course
        course_analysis = self.course_analyzer(
            course_profile=self._format_course_data(course)
        )
        
        # Step 2: Assess athlete vs course
        athlete_assessment = self.athlete_assessor(
            athlete_profile=self._format_athlete_data(athlete),
            course_analysis=course_analysis.analysis
        )
        
        # Step 3: Generate pacing strategy
        pacing_strategy = self.pacing_strategist(
            athlete_assessment=f"Strengths: {athlete_assessment.strengths_vs_course}\n"
                             f"Risks: {athlete_assessment.risk_areas}\n"
                             f"Power: {athlete_assessment.power_targets}",
            race_conditions=self._format_conditions_data(conditions)
        )
        
        # Step 4: Assess risks
        risk_assessment = self.risk_assessor(
            pacing_strategy=f"Swim: {pacing_strategy.swim_strategy}\n"
                          f"Bike: {pacing_strategy.bike_strategy}\n"
                          f"Run: {pacing_strategy.run_strategy}",
            race_conditions=self._format_conditions_data(conditions)
        )
        
        # Step 5: Optimize final strategy
        final_strategy = self.strategy_optimizer(
            course_analysis=course_analysis.analysis,
            athlete_assessment=athlete_assessment.strengths_vs_course,
            pacing_strategy=f"Swim: {pacing_strategy.swim_strategy}\n"
                           f"Bike: {pacing_strategy.bike_strategy}\n"
                           f"Run: {pacing_strategy.run_strategy}",
            risk_assessment=risk_assessment.mitigation_plan,
            target_time=athlete.target_finish_time or "Sub 6:00:00"
        )
        
        return {
            "course_analysis": course_analysis,
            "athlete_assessment": athlete_assessment,
            "pacing_strategy": pacing_strategy,
            "risk_assessment": risk_assessment,
            "final_strategy": final_strategy
        }
    
    def _format_course_data(self, course: CourseProfile) -> str:
        """Format course data for DSPy input"""
        climbs_text = "\n".join([
            f"- {climb.name}: Mile {climb.start_mile}-{climb.start_mile + climb.length_miles}, "
            f"{climb.avg_grade}% avg grade (max {climb.max_grade}%)"
            for climb in course.key_climbs
        ])
        
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

# ====================
# src/utils/config.py
import os
from dotenv import load_dotenv
import dspy

load_dotenv()

def setup_dspy_model():
    """Configure DSPy with the appropriate language model"""
    provider = os.getenv("DEFAULT_LM_PROVIDER", "openai").lower()
    
    if provider == "openai":
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        lm = dspy.OpenAI(model=model, max_tokens=1000)
    elif provider == "anthropic":
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        lm = dspy.Claude(model=model)
    elif provider == "together":
        lm = dspy.Together(model="mistralai/Mistral-7B-Instruct-v0.1")
    else:
        raise ValueError(f"Unsupported LM provider: {provider}")
    
    dspy.settings.configure(lm=lm)
    return lm

# ====================
# examples/basic_demo.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.course import CourseProfile, ClimbSegment
from src.models.athlete import AthleteProfile
from src.models.conditions import RaceConditions
from src.pipelines.core_strategy import RaceStrategyPipeline
from src.utils.config import setup_dspy_model

def main():
    """Demo the race strategy optimizer"""
    
    print("🏊‍♂️🚴‍♂️🏃‍♂️ DSPy Race Strategy Optimizer Demo")
    print("=" * 50)
    
    # Set up DSPy
    try:
        setup_dspy_model()
        print("✅ DSPy model configured successfully")
    except Exception as e:
        print(f"❌ Error setting up model: {e}")
        print("💡 Check your .env file and API keys")
        return
    
    # Create sample data
    happy_valley = CourseProfile(
        name="Ironman 70.3 Happy Valley",
        bike_distance_miles=56.0,
        bike_elevation_gain_ft=3500,
        swim_distance_miles=1.2,
        run_distance_miles=13.1,
        run_elevation_gain_ft=206,
        key_climbs=[
            ClimbSegment("Early Rolling Hills", 5, 10, 3, 6, 800),
            ClimbSegment("Hublers Ridge", 25, 5, 4, 8, 600),
            ClimbSegment("The Big Climb", 38, 3, 7, 12, 700),
            ClimbSegment("Final Hills to T2", 52, 4, 4, 7, 400)
        ],
        technical_sections=["Narrow park loop", "Multiple 90-degree turns"]
    )
    
    athlete = AthleteProfile(
        name="Alex Triathlete",
        ftp_watts=250,
        swim_pace_per_100m=90,
        run_threshold_pace=7.5,
        experience_level="intermediate",
        previous_70_3_time="5:45:00",
        strengths=["bike", "run"],
        limiters=["swim"],
        target_finish_time="5:30:00"
    )
    
    conditions = RaceConditions(
        temperature_f=75,
        wind_speed_mph=8,
        wind_direction="variable",
        precipitation="none",
        humidity_percent=65
    )
    
    # Generate strategy
    pipeline = RaceStrategyPipeline()
    
    try:
        print("🔄 Generating race strategy...")
        results = pipeline.generate_strategy(happy_valley, athlete, conditions)
        
        print("\n📊 RACE STRATEGY RESULTS")
        print("=" * 50)
        
        print(f"\n🎯 Final Strategy:\n{results['final_strategy'].final_strategy}")
        print(f"\n⏱️  Time Prediction:\n{results['final_strategy'].time_prediction}")
        print(f"\n📈 Success Probability: {results['final_strategy'].success_probability}")
        print(f"\n🔑 Key Success Factors:\n{results['final_strategy'].key_success_factors}")
        
    except Exception as e:
        print(f"❌ Error generating strategy: {e}")

if __name__ == "__main__":
    main()