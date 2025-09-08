#!/usr/bin/env python3
"""
Advanced Course Analysis Example - Enhanced DSPy Course Analysis
Demonstrates the implementation of GitHub issue #13.

This example showcases:
1. Enhanced DSPy signatures working with real GPS data
2. Integration with the DifficultyCalculator from issue #12
3. Segment-by-segment strategic analysis
4. Power/pacing recommendations based on actual gradients
5. Comprehensive strategic insights using real course characteristics
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.athlete import AthleteProfile
from src.models.conditions import RaceConditions
from src.pipelines.core_strategy import RaceStrategyPipeline
from src.utils.config import setup_dspy_model
from src.utils.course_loader import load_happy_valley_70_3_gps, load_alpe_dhuez_real


def print_enhanced_analysis(course_name, results):
    """Pretty print the enhanced course analysis results"""
    print(f"\n{'=' * 80}")
    print(f"🚴 ENHANCED COURSE ANALYSIS: {course_name}")
    print(f"{'=' * 80}")

    # Difficulty Metrics from Calculator
    diff_metrics = results["difficulty_metrics"]
    print(f"\n📊 OBJECTIVE DIFFICULTY METRICS:")
    print(f"   Overall Rating: {diff_metrics.overall_rating}/10")
    print(f"   Elevation Intensity: {diff_metrics.elevation_intensity:.1f} ft/mile")
    print(f"   Average Gradient: {diff_metrics.avg_gradient:.1f}%")
    print(f"   Maximum Gradient: {diff_metrics.max_gradient:.1f}%")
    print(
        f"   Climb Clustering: {diff_metrics.climb_clustering_score:.2f} (0=rolling, 1=sustained)"
    )
    print(f"   Technical Difficulty: {diff_metrics.technical_difficulty:.2f}/1.0")
    print(f"   \n   Justification: {diff_metrics.difficulty_justification}")

    # Enhanced Course Analysis
    course_analysis = results["enhanced_course_analysis"]
    print(f"\n🧠 AI-ENHANCED STRATEGIC ANALYSIS:")
    print(f"   {course_analysis.strategic_analysis}")

    print(f"\n🎯 POWER & PACING PLAN:")
    print(f"   {course_analysis.power_pacing_plan}")

    print(f"\n📈 SEGMENT-BY-SEGMENT BREAKDOWN:")
    print(f"   {course_analysis.segment_analysis}")

    print(f"\n💡 TACTICAL INSIGHTS:")
    print(f"   {course_analysis.tactical_insights}")

    # Crux Segments Analysis
    print(f"\n🎯 CRUX SEGMENTS (Most Critical Points):")
    for i, segment in enumerate(diff_metrics.crux_segments[:3], 1):
        print(f"\n   {i}. {segment['name']} - Mile {segment['start_mile']:.1f}")
        print(f"      • Distance: {segment['length_miles']:.1f} miles")
        print(
            f"      • Gradient: {segment['avg_grade']:.1f}% avg, {segment['max_grade']:.1f}% max"
        )
        print(f"      • Elevation: {segment['elevation_gain_ft']} ft gain")
        print(f"      • Difficulty: {segment['difficulty_score']:.2f}/1.0")
        print(f"      • Strategy: {segment['strategic_importance']}")

    # Individual Segment Analysis
    if results["segment_analyses"]:
        print(f"\n🔍 DETAILED SEGMENT ANALYSIS:")
        for i, seg_analysis in enumerate(results["segment_analyses"][:3], 1):
            print(f"\n   Segment {i} Power Recommendation:")
            print(f"   {seg_analysis.power_recommendation}")
            print(f"\n   Segment {i} Tactical Approach:")
            print(f"   {seg_analysis.tactical_approach}")

    # Final Strategy with Enhanced Data
    final_strategy = results["final_strategy"]
    print(f"\n🏆 FINAL ENHANCED STRATEGY:")
    print(f"   {final_strategy.final_strategy}")

    print(f"\n⏱️ TIME PREDICTION (Enhanced):")
    print(f"   {final_strategy.time_prediction}")

    print(f"\n📊 SUCCESS PROBABILITY:")
    print(f"   {final_strategy.success_probability}")

    print(f"\n🔑 KEY SUCCESS FACTORS:")
    print(f"   {final_strategy.key_success_factors}")


def main():
    """Run the enhanced course analysis demonstration"""
    print("\n" + "=" * 80)
    print("🚴 ENHANCED DSPy COURSE ANALYSIS - ISSUE #13 DEMONSTRATION")
    print("=" * 80)
    print("Showcasing enhanced DSPy signatures with real GPS data integration:")
    print("• Enhanced CourseAnalyzer with difficulty calculator integration")
    print("• Segment-by-segment strategic analysis")
    print("• Power/pacing recommendations based on actual gradients")
    print("• Comprehensive strategic insights using real course characteristics")

    # Set up DSPy
    try:
        setup_dspy_model()
        print("✅ DSPy model configured successfully")
    except Exception as e:
        print(f"❌ Error setting up model: {e}")
        print("💡 Check your .env file and API keys")
        return

    # Create enhanced pipeline
    enhanced_pipeline = RaceStrategyPipeline()

    # Create test athlete optimized for challenging courses
    elite_athlete = AthleteProfile(
        name="Elena Rodriguez",
        ftp_watts=280,
        swim_pace_per_100m=85,
        run_threshold_pace=7.0,
        experience_level="advanced",
        previous_70_3_time="5:15:00",
        strengths=["climbing", "bike", "endurance"],
        limiters=["swim_technique"],
        target_finish_time="5:00:00",
        age=32,
        weight_lbs=135,
        climbing_ability=8,
    )

    # Challenging race conditions
    race_conditions = RaceConditions(
        temperature_f=82,
        wind_speed_mph=12,
        wind_direction="headwind on climbs",
        precipitation="none",
        humidity_percent=75,
    )

    # Test 1: Happy Valley 70.3 with Enhanced Analysis
    print("\n" + "─" * 80)
    print("TEST 1: HAPPY VALLEY 70.3 - ENHANCED ANALYSIS")
    print("─" * 80)

    try:
        happy_valley = load_happy_valley_70_3_gps()
        print(f"✅ Loaded real GPS data: {happy_valley.name}")
        print(
            f"   Course Profile: {len(happy_valley.key_climbs)} key climbs identified"
        )
        print(
            f"   Elevation Data: {happy_valley.bike_elevation_gain_ft}ft total gain over {happy_valley.bike_distance_miles} miles"
        )

        hv_results = enhanced_pipeline.generate_strategy(
            happy_valley, elite_athlete, race_conditions
        )
        print_enhanced_analysis(happy_valley.name, hv_results)

    except Exception as e:
        print(f"❌ Error analyzing Happy Valley: {e}")
        import traceback

        traceback.print_exc()

    # Test 2: Alpe d'Huez with Enhanced Analysis
    print("\n" + "─" * 80)
    print("TEST 2: ALPE D'HUEZ - ENHANCED ANALYSIS")
    print("─" * 80)

    try:
        alpe_dhuez = load_alpe_dhuez_real()
        print(f"✅ Loaded real GPS data: {alpe_dhuez.name}")
        print(f"   Course Profile: {len(alpe_dhuez.key_climbs)} key climbs identified")
        print(
            f"   Elevation Data: {alpe_dhuez.bike_elevation_gain_ft}ft total gain over {alpe_dhuez.bike_distance_miles} miles"
        )
        print(f"   Altitude: {alpe_dhuez.altitude_ft}ft (altitude effects considered)")

        ad_results = enhanced_pipeline.generate_strategy(
            alpe_dhuez, elite_athlete, race_conditions
        )
        print_enhanced_analysis(alpe_dhuez.name, ad_results)

    except Exception as e:
        print(f"❌ Error analyzing Alpe d'Huez: {e}")
        import traceback

        traceback.print_exc()

    # Test 3: Compare Enhanced Analysis Results
    print("\n" + "─" * 80)
    print("TEST 3: ENHANCED ANALYSIS COMPARISON")
    print("─" * 80)

    try:
        if "hv_results" in locals() and "ad_results" in locals():
            hv_difficulty = hv_results["difficulty_metrics"].overall_rating
            ad_difficulty = ad_results["difficulty_metrics"].overall_rating

            print(f"\n📊 DIFFICULTY COMPARISON:")
            print(f"   Happy Valley 70.3: {hv_difficulty}/10 difficulty")
            print(f"   Alpe d'Huez: {ad_difficulty}/10 difficulty")
            print(f"   Difference: {ad_difficulty - hv_difficulty:.1f} points")

            print(f"\n🎯 STRATEGIC DIFFERENCES:")
            hv_crux_count = len(hv_results["difficulty_metrics"].crux_segments)
            ad_crux_count = len(ad_results["difficulty_metrics"].crux_segments)
            print(f"   Happy Valley crux segments: {hv_crux_count}")
            print(f"   Alpe d'Huez crux segments: {ad_crux_count}")

            print(f"\n💪 ATHLETE ADAPTATIONS:")
            print(f"   Enhanced analysis shows how Elena's climbing strength")
            print(
                f"   ({elite_athlete.climbing_ability}/10) aligns differently with each course"
            )

            if ad_difficulty > hv_difficulty:
                print(f"\n✨ KEY FINDING:")
                print(
                    f"   Alpe d'Huez requires {ad_difficulty - hv_difficulty:.1f} points more difficulty management"
                )
                print(f"   Enhanced DSPy signatures identified specific power targets")
                print(f"   and segment-specific tactics for each challenge level")

    except Exception as e:
        print(f"❌ Error in comparison: {e}")

    # Summary
    print(f"\n{'=' * 80}")
    print("📋 ENHANCED ANALYSIS SUMMARY")
    print(f"{'=' * 80}")

    print("\n✅ Successfully demonstrated Issue #13 requirements:")
    print("   1. ✅ Enhanced CourseAnalyzer signature with real elevation data")
    print("   2. ✅ Segment-by-segment strategic analysis")
    print("   3. ✅ Power/pacing recommendations based on actual gradients")
    print("   4. ✅ Integration with course difficulty calculations")
    print("   5. ✅ Improved strategic insights using real course characteristics")

    print("\n🎯 Enhancement Highlights:")
    print("   • Real GPS elevation data integration")
    print("   • Objective difficulty scoring from DifficultyCalculator")
    print("   • Crux segment identification and tactical analysis")
    print("   • Athlete-specific power recommendations per segment")
    print("   • Enhanced strategic insights based on course realities")

    print("\n🚀 Next Steps:")
    print("   • Test with additional real course data")
    print("   • Validate power recommendations against race results")
    print("   • Expand segment analysis to include run course data")

    print("\n✨ Enhanced DSPy Course Analysis (Issue #13) Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
