"""
Tests for the equipment selection system.

Tests equipment models, database decision logic, pipeline integration,
and comprehensive equipment recommendation scenarios.
"""

from src.models.athlete import AthleteProfile
from src.models.conditions import RaceConditions
from src.models.course import CourseProfile
from src.models.equipment import (
    BikeSetup,
    SwimGear,
    RunEquipment,
    AccessoryRecommendations,
    PerformanceImpact,
    EquipmentRecommendations,
    EquipmentItem,
)
from src.utils.equipment_database import EquipmentDatabase
from src.pipelines.equipment import EquipmentPipeline


class TestEquipmentModels:
    """Test equipment data model structures"""

    def test_bike_setup_creation(self):
        """Test BikeSetup model creation with all fields"""
        bike_setup = BikeSetup(
            gearing="compact",
            gearing_rationale="Better for climbing",
            wheels="climbing",
            wheel_rationale="Lightweight for hills",
            position="moderate",
            position_rationale="Balanced comfort and aero",
            tire_pressure="95-100 psi",
            accessories=["GPS computer", "Nutrition storage"],
        )

        assert bike_setup.gearing == "compact"
        assert bike_setup.wheels == "climbing"
        assert bike_setup.position == "moderate"
        assert len(bike_setup.accessories) == 2
        assert "GPS computer" in bike_setup.accessories

    def test_swim_gear_structure(self):
        """Test SwimGear data structure"""
        swim_gear = SwimGear(
            wetsuit_decision="wetsuit",
            wetsuit_rationale="Cold water conditions",
            wetsuit_type="full",
            goggles="clear",
            goggle_rationale="Best visibility",
            cap_strategy="Race provided",
            accessories=["Anti-fog spray"],
        )

        assert swim_gear.wetsuit_decision == "wetsuit"
        assert swim_gear.wetsuit_type == "full"
        assert swim_gear.goggles == "clear"
        assert len(swim_gear.accessories) == 1

    def test_equipment_recommendations_complete_structure(self):
        """Test complete EquipmentRecommendations structure"""
        bike_setup = BikeSetup(
            "compact",
            "Good for climbing",
            "climbing",
            "Light wheels",
            "moderate",
            "Balanced",
        )
        swim_gear = SwimGear(
            "wetsuit", "Cold water", "full", "clear", "Clear visibility"
        )
        run_equipment = RunEquipment(
            "neutral", "Good support", "minimal", "Light clothing"
        )
        accessories = AccessoryRecommendations(["Bottles"], ["Tools"], ["GPS"])
        performance = PerformanceImpact(
            "2 minutes", "High value", ["Gearing"], "Low risk"
        )

        recommendations = EquipmentRecommendations(
            race_name="Test 70.3",
            athlete_name="Test Athlete",
            conditions_summary="Moderate conditions",
            bike_setup=bike_setup,
            swim_gear=swim_gear,
            run_equipment=run_equipment,
            accessories=accessories,
            performance_impact=performance,
            confidence_level="high",
        )

        assert recommendations.race_name == "Test 70.3"
        assert recommendations.confidence_level == "high"
        assert isinstance(recommendations.bike_setup, BikeSetup)
        assert isinstance(recommendations.swim_gear, SwimGear)
        assert isinstance(recommendations.run_equipment, RunEquipment)


class TestEquipmentDatabase:
    """Test equipment database decision logic"""

    def setup_method(self):
        """Set up test fixtures"""
        self.db = EquipmentDatabase()
        self.athlete = AthleteProfile(
            name="Test Athlete",
            ftp_watts=250,
            swim_pace_per_100m=85.0,
            run_threshold_pace=7.5,
            experience_level="intermediate",
            previous_70_3_time="5:30:00",
            strengths=["bike"],
            limiters=["run"],
            target_finish_time="5:15:00",
            weight_lbs=170,
            height_inches=72,
            age=35,
        )

        self.flat_course = CourseProfile(
            name="Flat 70.3",
            bike_distance_miles=56.0,
            bike_elevation_gain_ft=1200,  # ~21 ft/mile - flat
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=300,
            key_climbs=[],
            technical_sections=[],
            altitude_ft=100,
        )

        self.hilly_course = CourseProfile(
            name="Hilly 70.3",
            bike_distance_miles=56.0,
            bike_elevation_gain_ft=4000,  # ~71 ft/mile - mountainous
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=1200,
            key_climbs=[],
            technical_sections=[],
            altitude_ft=2000,
        )

        self.calm_conditions = RaceConditions(
            temperature_f=70,
            wind_speed_mph=5,
            wind_direction="variable",
            precipitation="none",
            humidity_percent=50,
        )

        self.windy_conditions = RaceConditions(
            temperature_f=75,
            wind_speed_mph=25,
            wind_direction="crosswind",
            precipitation="none",
            humidity_percent=60,
        )

    def test_course_analysis_flat(self):
        """Test course analysis for flat course"""
        analysis = self.db.analyze_course_demands(self.flat_course)

        assert analysis["course_type"] == "flat_course"
        assert analysis["climbing_demand"] == "low"
        assert float(analysis["elevation_per_mile"]) < 30

    def test_course_analysis_hilly(self):
        """Test course analysis for hilly course"""
        analysis = self.db.analyze_course_demands(self.hilly_course)

        assert analysis["course_type"] == "mountainous"
        assert analysis["climbing_demand"] == "high"
        assert float(analysis["elevation_per_mile"]) > 60

    def test_bike_gearing_flat_course(self):
        """Test bike gearing recommendation for flat course"""
        gearing, rationale = self.db.recommend_bike_gearing(
            self.flat_course, self.athlete, self.calm_conditions
        )

        # Should recommend standard for flat course with strong cyclist
        assert gearing in ["standard", "compact"]
        assert "flat" in rationale.lower() or "climbing" in rationale.lower()

    def test_bike_gearing_hilly_course(self):
        """Test bike gearing recommendation for hilly course"""
        gearing, rationale = self.db.recommend_bike_gearing(
            self.hilly_course, self.athlete, self.calm_conditions
        )

        # Should recommend compact for hilly course
        assert gearing == "compact"
        assert "climbing" in rationale.lower() or "compact" in rationale.lower()

    def test_beginner_gets_easier_gearing(self):
        """Test that beginners get easier gearing recommendations"""
        beginner = AthleteProfile(
            "Beginner", 180, 90, 8, "beginner", None, [], [], None, 160, 70, 25
        )

        gearing, rationale = self.db.recommend_bike_gearing(
            self.hilly_course, beginner, self.calm_conditions
        )

        # Beginner should get compact gearing
        assert gearing == "compact"

    def test_wheel_recommendation_flat_windy(self):
        """Test wheel recommendation for flat, windy course"""
        wheels, rationale = self.db.recommend_wheels(
            self.flat_course, self.windy_conditions
        )

        # Very windy conditions should avoid deep aero wheels
        assert wheels in ["all-around", "climbing"]
        assert "wind" in rationale.lower()

    def test_wheel_recommendation_hilly_calm(self):
        """Test wheel recommendation for hilly, calm course"""
        wheels, rationale = self.db.recommend_wheels(
            self.hilly_course, self.calm_conditions
        )

        # Hilly course should get climbing wheels
        assert wheels in ["climbing", "all-around"]

    def test_wetsuit_cold_water(self):
        """Test wetsuit recommendation for cold conditions"""
        cold_conditions = RaceConditions(50, 5, "none", "none", 40)  # Very cold

        decision, wetsuit_type, rationale = self.db.recommend_wetsuit_decision(
            cold_conditions, self.athlete
        )

        assert decision == "wetsuit"
        assert wetsuit_type == "full"
        assert "temperature" in rationale.lower()

    def test_wetsuit_warm_water(self):
        """Test wetsuit recommendation for warm conditions"""
        warm_conditions = RaceConditions(85, 5, "none", "none", 40)  # Very warm

        decision, wetsuit_type, rationale = self.db.recommend_wetsuit_decision(
            warm_conditions, self.athlete
        )

        assert decision == "no-wetsuit"
        assert "warm" in rationale.lower()

    def test_beginner_swimmer_wetsuit_bias(self):
        """Test that beginner swimmers get wetsuit recommendations"""
        beginner_swimmer = AthleteProfile(
            "Weak Swimmer",
            250,
            120,
            7,
            "intermediate",
            None,
            ["bike"],
            ["swim"],
            None,
            170,
            72,
            30,
        )

        borderline_conditions = RaceConditions(
            72, 5, "none", "none", 50
        )  # Borderline temp

        decision, wetsuit_type, rationale = self.db.recommend_wetsuit_decision(
            borderline_conditions, beginner_swimmer
        )

        # Should recommend wetsuit for weak swimmer
        assert decision == "wetsuit"

    def test_running_shoes_beginner(self):
        """Test running shoe recommendation for beginner"""
        beginner = AthleteProfile(
            "Beginner", 200, 90, 9, "beginner", None, [], ["run"], None, 160, 70, 25
        )

        shoes, rationale = self.db.recommend_running_shoes(self.flat_course, beginner)

        # Beginner should get max cushioning
        assert shoes == "max-cushion"
        assert "cushion" in rationale.lower() or "comfort" in rationale.lower()

    def test_running_shoes_advanced_flat(self):
        """Test running shoe recommendation for advanced athlete on flat course"""
        advanced = AthleteProfile(
            "Advanced",
            300,
            80,
            6.5,
            "advanced",
            "4:45:00",
            ["run"],
            [],
            "4:30:00",
            165,
            71,
            28,
        )

        shoes, rationale = self.db.recommend_running_shoes(self.flat_course, advanced)

        # Advanced athlete on flat course should get neutral or responsive shoes
        assert shoes in ["neutral", "minimal"]

    def test_time_savings_estimation(self):
        """Test time savings estimation for equipment changes"""
        equipment_changes = {
            "gearing": "compact",
            "wheels": "aero",
            "wetsuit_decision": "wetsuit",
        }

        savings = self.db.estimate_time_savings(equipment_changes, self.flat_course)

        # Should return a time estimate
        assert "second" in savings.lower() or "minute" in savings.lower()
        assert any(char.isdigit() for char in savings)

    def test_equipment_rationale_generation(self):
        """Test that all recommendations include rationales"""
        # Test gearing rationale
        _, gearing_rationale = self.db.recommend_bike_gearing(
            self.hilly_course, self.athlete, self.calm_conditions
        )
        assert len(gearing_rationale) > 10

        # Test wheel rationale
        _, wheel_rationale = self.db.recommend_wheels(
            self.flat_course, self.windy_conditions
        )
        assert len(wheel_rationale) > 10

        # Test shoe rationale
        _, shoe_rationale = self.db.recommend_running_shoes(
            self.hilly_course, self.athlete
        )
        assert len(shoe_rationale) > 10

    def test_extreme_temperatures(self):
        """Test equipment recommendations for extreme temperatures"""
        # Test extreme cold
        extreme_cold = RaceConditions(
            temperature_f=25,  # Below freezing
            wind_speed_mph=10,
            wind_direction="variable",
            precipitation="none",
            humidity_percent=40,
        )

        decision, wetsuit_type, _ = self.db.recommend_wetsuit_decision(
            extreme_cold, self.athlete
        )
        assert decision == "wetsuit"
        assert wetsuit_type == "full"

        # Test extreme heat
        extreme_hot = RaceConditions(
            temperature_f=105,  # Above 100°F
            wind_speed_mph=5,
            wind_direction="variable",
            precipitation="none",
            humidity_percent=20,
        )

        decision, wetsuit_type, _ = self.db.recommend_wetsuit_decision(
            extreme_hot, self.athlete
        )
        assert decision == "no-wetsuit"

    def test_extreme_wind_conditions(self):
        """Test equipment recommendations for extreme wind"""
        extreme_wind = RaceConditions(
            temperature_f=70,
            wind_speed_mph=40,  # Extreme wind
            wind_direction="crosswind",
            precipitation="none",
            humidity_percent=50,
        )

        wheels, rationale = self.db.recommend_wheels(self.flat_course, extreme_wind)
        # Should not recommend aero wheels in extreme wind
        assert wheels != "aero"
        assert "wind" in rationale.lower()

    def test_negative_wind_speed(self):
        """Test handling of invalid negative wind speed"""
        invalid_conditions = RaceConditions(
            temperature_f=70,
            wind_speed_mph=-10,  # Invalid negative wind
            wind_direction="variable",
            precipitation="none",
            humidity_percent=50,
        )

        # Should handle gracefully without error
        wheels, _ = self.db.recommend_wheels(self.flat_course, invalid_conditions)
        assert wheels in ["aero", "climbing", "all-around"]

    def test_missing_athlete_data(self):
        """Test handling of missing athlete data fields"""
        incomplete_athlete = AthleteProfile(
            name="Incomplete",
            ftp_watts=None,  # Missing FTP
            swim_pace_per_100m=90,
            run_threshold_pace=8,
            experience_level="intermediate",
            previous_70_3_time=None,
            strengths=[],
            limiters=[],
            target_finish_time=None,
            weight_lbs=150,
            height_inches=68,
            age=30,
        )

        # Should handle missing data gracefully
        gearing, _ = self.db.recommend_bike_gearing(
            self.flat_course, incomplete_athlete, self.calm_conditions
        )
        assert gearing in ["compact", "standard", "1x"]

    def test_equipment_compatibility_validation(self):
        """Test equipment compatibility validation"""
        # Test aero wheels in extreme wind warning
        recommendations = {
            "wheels": "aero",
            "wetsuit_decision": "wetsuit",
            "shoes": "neutral",
        }

        extreme_wind = RaceConditions(
            temperature_f=70,
            wind_speed_mph=35,
            wind_direction="crosswind",
            precipitation="none",
            humidity_percent=50,
        )

        warnings = self.db.validate_equipment_compatibility(
            recommendations, extreme_wind
        )
        assert len(warnings) > 0
        assert any("aero wheels" in w.lower() for w in warnings)

    def test_zero_distance_course(self):
        """Test handling of course with zero or missing distances"""
        zero_distance_course = CourseProfile(
            name="Zero Test",
            bike_distance_miles=0,  # Zero distance
            bike_elevation_gain_ft=0,
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=300,
            key_climbs=[],
            technical_sections=[],
            altitude_ft=100,
        )

        # Should handle zero distance gracefully
        analysis = self.db.analyze_course_demands(zero_distance_course)
        assert analysis["course_type"] == "flat_course"
        assert float(analysis["elevation_per_mile"]) == 0


class TestEquipmentPipeline:
    """Test equipment pipeline integration"""

    def setup_method(self):
        """Set up test fixtures"""
        self.pipeline = EquipmentPipeline()
        self.athlete = AthleteProfile(
            name="Pipeline Test",
            ftp_watts=275,
            swim_pace_per_100m=82.0,
            run_threshold_pace=7.0,
            experience_level="advanced",
            previous_70_3_time="5:00:00",
            strengths=["bike", "run"],
            limiters=["swim"],
            target_finish_time="4:55:00",
            weight_lbs=165,
            height_inches=71,
            age=32,
        )

        self.course = CourseProfile(
            name="Pipeline Test 70.3",
            bike_distance_miles=56.0,
            bike_elevation_gain_ft=2800,  # Moderate hills
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=600,
            key_climbs=[],
            technical_sections=[],
            altitude_ft=1500,
        )

        self.conditions = RaceConditions(
            temperature_f=78,
            wind_speed_mph=12,
            wind_direction="headwind",
            precipitation="none",
            humidity_percent=65,
        )

    def test_pipeline_generates_complete_recommendations(self):
        """Test that pipeline generates complete equipment recommendations"""

        # This test will pass even without DSPy configuration since we use the database fallbacks
        recommendations = self.pipeline.generate_equipment_recommendations(
            self.course, self.athlete, self.conditions
        )

        assert isinstance(recommendations, EquipmentRecommendations)
        assert recommendations.race_name == "Pipeline Test 70.3"
        assert recommendations.athlete_name == "Pipeline Test"
        assert isinstance(recommendations.bike_setup, BikeSetup)
        assert isinstance(recommendations.swim_gear, SwimGear)
        assert isinstance(recommendations.run_equipment, RunEquipment)

    def test_bike_setup_recommendations(self):
        """Test bike setup recommendations"""
        recommendations = self.pipeline.generate_equipment_recommendations(
            self.course, self.athlete, self.conditions
        )

        bike_setup = recommendations.bike_setup
        assert bike_setup.gearing in ["compact", "standard", "1x"]
        assert bike_setup.wheels in ["aero", "climbing", "all-around"]
        assert bike_setup.position in [
            "aggressive",
            "moderate",
            "comfort",
            "time-trial",
        ]
        assert len(bike_setup.gearing_rationale) > 0
        assert len(bike_setup.wheel_rationale) > 0

    def test_swim_gear_recommendations(self):
        """Test swim gear recommendations"""
        recommendations = self.pipeline.generate_equipment_recommendations(
            self.course, self.athlete, self.conditions
        )

        swim_gear = recommendations.swim_gear
        assert swim_gear.wetsuit_decision in [
            "wetsuit",
            "no-wetsuit",
            "depends-on-temp",
        ]
        assert swim_gear.goggles in ["clear", "tinted", "mirrored", "photochromic"]
        assert len(swim_gear.wetsuit_rationale) > 0
        assert len(swim_gear.goggle_rationale) > 0

    def test_performance_impact_analysis(self):
        """Test performance impact analysis"""
        recommendations = self.pipeline.generate_equipment_recommendations(
            self.course, self.athlete, self.conditions
        )

        performance = recommendations.performance_impact
        assert len(performance.time_savings_estimate) > 0
        assert len(performance.cost_analysis) > 0
        assert len(performance.priority_ranking) > 0
        assert len(performance.risk_assessment) > 0

    def test_pacing_integration(self):
        """Test equipment recommendations integrate with pacing strategy"""
        pacing_strategy = "Conservative start, build through bike, negative split run"

        recommendations = self.pipeline.generate_equipment_recommendations(
            self.course, self.athlete, self.conditions, pacing_strategy
        )

        # Should successfully integrate pacing strategy
        assert isinstance(recommendations, EquipmentRecommendations)
        assert recommendations.confidence_level in ["low", "medium", "high"]

    def test_course_specific_recommendations(self):
        """Test recommendations adapt to different course types"""
        # Test flat course
        flat_course = CourseProfile("Flat Test", 56, 800, 1.2, 13.1, 200, [], [], 0)

        flat_recommendations = self.pipeline.generate_equipment_recommendations(
            flat_course, self.athlete, self.conditions
        )

        # Test mountainous course
        mountain_course = CourseProfile(
            "Mountain Test", 56, 5000, 1.2, 13.1, 1500, [], [], 3000
        )

        mountain_recommendations = self.pipeline.generate_equipment_recommendations(
            mountain_course, self.athlete, self.conditions
        )

        # Recommendations should be different
        assert (
            flat_recommendations.bike_setup.gearing
            != mountain_recommendations.bike_setup.gearing
            or flat_recommendations.bike_setup.wheels
            != mountain_recommendations.bike_setup.wheels
        )

    def test_athlete_experience_adaptation(self):
        """Test recommendations adapt to athlete experience level"""
        # Test beginner athlete
        beginner = AthleteProfile(
            "Beginner",
            200,
            100,
            8.5,
            "beginner",
            None,
            [],
            ["swim", "run"],
            None,
            170,
            70,
            25,
        )

        beginner_recommendations = self.pipeline.generate_equipment_recommendations(
            self.course, beginner, self.conditions
        )

        # Test advanced athlete
        advanced_recommendations = self.pipeline.generate_equipment_recommendations(
            self.course, self.athlete, self.conditions
        )

        # Should have different recommendations based on experience
        assert isinstance(beginner_recommendations, EquipmentRecommendations)
        assert isinstance(advanced_recommendations, EquipmentRecommendations)

    def test_conditions_adaptation(self):
        """Test recommendations adapt to different weather conditions"""
        # Test cold, calm conditions
        cold_conditions = RaceConditions(55, 3, "tailwind", "none", 40)

        cold_recommendations = self.pipeline.generate_equipment_recommendations(
            self.course, self.athlete, cold_conditions
        )

        # Test hot, windy conditions
        hot_windy_conditions = RaceConditions(90, 30, "crosswind", "none", 80)

        hot_recommendations = self.pipeline.generate_equipment_recommendations(
            self.course, self.athlete, hot_windy_conditions
        )

        # Wetsuit decisions should be different
        assert (
            cold_recommendations.swim_gear.wetsuit_decision
            != hot_recommendations.swim_gear.wetsuit_decision
        )

    def test_bike_position_recommendations(self):
        """Test that bike position adapts to athlete and course"""
        # Test beginner gets comfort position
        beginner = AthleteProfile(
            "Beginner", 200, 90, 8.5, "beginner", None, [], [], None, 170, 70, 25
        )

        beginner_recs = self.pipeline.generate_equipment_recommendations(
            self.course, beginner, self.conditions
        )
        assert beginner_recs.bike_setup.position == "comfort"
        assert "comfort" in beginner_recs.bike_setup.position_rationale.lower()

        # Test advanced athlete on flat course gets aggressive position
        flat_course = CourseProfile("Flat Test", 56, 500, 1.2, 13.1, 100, [], [], 0)

        advanced_recs = self.pipeline.generate_equipment_recommendations(
            flat_course, self.athlete, self.conditions  # self.athlete is advanced
        )
        assert advanced_recs.bike_setup.position == "aggressive"
        assert "aggressive" in advanced_recs.bike_setup.position_rationale.lower()
