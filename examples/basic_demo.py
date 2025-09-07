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