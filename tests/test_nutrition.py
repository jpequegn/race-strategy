"""
Tests for the nutrition strategy module.

Tests both the calculation utilities and DSPy pipeline integration
for triathlon race nutrition planning.
"""

# Test imports
from src.models.athlete import AthleteProfile
from src.models.conditions import RaceConditions
from src.models.nutrition import (
    ContingencyNutrition,
    ElectrolyteStrategy,
    FuelingSchedule,
    HydrationPlan,
    NutritionItem,
    NutritionPlan,
)
from src.utils.nutrition_calculator import NutritionCalculator


class TestNutritionModels:
    """Test nutrition data model structures"""

    def test_nutrition_item_creation(self):
        """Test NutritionItem creation with all fields"""
        item = NutritionItem(
            time_hours=1.5,
            item_type="gel",
            product_name="GU Energy Gel",
            quantity="1 gel",
            calories=100,
            carbs_g=22,
            sodium_mg=60,
            notes="Take with water",
        )

        assert item.time_hours == 1.5
        assert item.item_type == "gel"
        assert item.product_name == "GU Energy Gel"
        assert item.calories == 100
        assert item.carbs_g == 22
        assert item.sodium_mg == 60
        assert item.notes == "Take with water"

    def test_hydration_plan_structure(self):
        """Test HydrationPlan data structure"""
        items = [NutritionItem(1.0, "fluid", "Water", "16 oz", 0, 0, 0)]
        plan = HydrationPlan(
            total_fluid_oz=120,
            hourly_targets=[20, 24, 24, 24, 24],
            items=items,
            sweat_rate_oz_per_hour=28.0,
            replacement_percentage=85,
        )

        assert plan.total_fluid_oz == 120
        assert len(plan.hourly_targets) == 5
        assert plan.sweat_rate_oz_per_hour == 28.0
        assert plan.replacement_percentage == 85
        assert len(plan.items) == 1

    def test_nutrition_plan_complete_structure(self):
        """Test complete NutritionPlan structure with all components"""
        # Create mock components
        hydration = HydrationPlan(100, [20, 20, 20, 20, 20], [], 25.0, 80)
        fueling = FuelingSchedule(60, 1500, [])
        electrolytes = ElectrolyteStrategy(1800, [300, 300, 300, 300, 300], [])
        contingency = ContingencyNutrition(
            [], "Reduce intake", [], [], "Use aid station"
        )

        plan = NutritionPlan(
            race_duration_hours=5.0,
            athlete_weight_lbs=160.0,
            conditions_summary="Hot and humid",
            hydration_plan=hydration,
            fueling_schedule=fueling,
            electrolyte_strategy=electrolytes,
            contingency_nutrition=contingency,
        )

        assert plan.race_duration_hours == 5.0
        assert plan.athlete_weight_lbs == 160.0
        assert plan.conditions_summary == "Hot and humid"
        assert plan.sports_nutrition_compliance is True
        assert isinstance(plan.hydration_plan, HydrationPlan)
        assert isinstance(plan.fueling_schedule, FuelingSchedule)


class TestNutritionCalculator:
    """Test nutrition calculation utilities"""

    def setup_method(self):
        """Set up test fixtures"""
        self.calculator = NutritionCalculator()
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

        self.hot_conditions = RaceConditions(
            temperature_f=85,
            wind_speed_mph=5,
            wind_direction="headwind",
            precipitation="none",
            humidity_percent=70,
        )

        self.cool_conditions = RaceConditions(
            temperature_f=65,
            wind_speed_mph=10,
            wind_direction="tailwind",
            precipitation="none",
            humidity_percent=45,
        )

    def test_sweat_rate_calculation_baseline(self):
        """Test sweat rate calculation with baseline conditions"""
        # Cool conditions, average weight athlete
        baseline_athlete = AthleteProfile(
            "Baseline",
            200,
            90.0,
            8.0,
            "intermediate",
            None,
            [],
            [],
            None,
            150,
            70,
            30,  # 150 lbs = reference weight
        )

        baseline_conditions = RaceConditions(68, 5, "variable", "none", 40)
        sweat_rate = self.calculator.calculate_sweat_rate(
            baseline_athlete, baseline_conditions
        )

        # Should be close to baseline rate for reference conditions
        assert 18 <= sweat_rate <= 22

    def test_sweat_rate_hot_conditions(self):
        """Test sweat rate increases with hot/humid conditions"""
        cool_sweat = self.calculator.calculate_sweat_rate(
            self.athlete, self.cool_conditions
        )
        hot_sweat = self.calculator.calculate_sweat_rate(
            self.athlete, self.hot_conditions
        )

        # Hot conditions should increase sweat rate
        assert hot_sweat > cool_sweat
        assert hot_sweat >= 22  # Should be significantly higher in heat

    def test_sweat_rate_weight_adjustment(self):
        """Test sweat rate adjusts for athlete weight"""
        light_athlete = AthleteProfile(
            "Light",
            200,
            90.0,
            8.0,
            "intermediate",
            None,
            [],
            [],
            None,
            130,
            66,
            25,  # 20 lbs lighter
        )

        light_sweat = self.calculator.calculate_sweat_rate(
            light_athlete, self.hot_conditions
        )
        heavy_sweat = self.calculator.calculate_sweat_rate(
            self.athlete, self.hot_conditions
        )

        # Heavier athletes should sweat more
        assert heavy_sweat > light_sweat

    def test_carb_needs_by_duration(self):
        """Test carbohydrate recommendations scale with race duration"""
        short_race = self.calculator.calculate_carb_needs(2.0, "moderate")  # 2 hours
        medium_race = self.calculator.calculate_carb_needs(3.0, "moderate")  # 3 hours
        long_race = self.calculator.calculate_carb_needs(4.0, "moderate")  # 4 hours

        # Longer races should have higher or equal carb recommendations
        assert short_race >= 30  # Minimum recommendation
        assert medium_race >= short_race
        assert long_race >= medium_race or long_race == 60  # May cap at standard 60g

    def test_carb_needs_by_intensity(self):
        """Test carbohydrate recommendations adjust for intensity"""
        moderate_carbs = self.calculator.calculate_carb_needs(3.0, "moderate")
        high_carbs = self.calculator.calculate_carb_needs(3.0, "high")

        # Higher intensity should require more carbs
        assert high_carbs >= moderate_carbs

    def test_sodium_needs_baseline(self):
        """Test sodium recommendations baseline calculation"""
        moderate_sweat_rate = 25.0
        sodium = self.calculator.calculate_sodium_needs(
            moderate_sweat_rate, self.cool_conditions, self.athlete
        )

        # Should be in reasonable physiological range
        assert 250 <= sodium <= 500

    def test_sodium_needs_hot_conditions(self):
        """Test sodium increases with hot conditions and high sweat rates"""
        high_sweat_rate = 35.0  # High sweat rate
        cool_sodium = self.calculator.calculate_sodium_needs(
            high_sweat_rate, self.cool_conditions, self.athlete
        )
        hot_sodium = self.calculator.calculate_sodium_needs(
            high_sweat_rate, self.hot_conditions, self.athlete
        )

        # Hot conditions should increase sodium needs
        assert hot_sodium > cool_sodium
        # Both should be in safe range
        assert hot_sodium <= 800  # Safety cap

    def test_fluid_replacement_calculation(self):
        """Test fluid replacement calculation"""
        sweat_rate = 30.0  # oz/hour
        fluid_per_hour, replacement_pct = self.calculator.calculate_fluid_replacement(
            sweat_rate
        )

        # Should replace 75-100% of sweat loss
        assert 75 <= replacement_pct <= 100
        assert 20 <= fluid_per_hour <= 32  # Practical gastric emptying limits

        # Check calculation consistency
        expected_fluid = int(sweat_rate * (replacement_pct / 100))
        assert abs(fluid_per_hour - expected_fluid) <= 2  # Allow for practical limits

    def test_hourly_schedule_generation(self):
        """Test generation of hour-by-hour nutrition schedule"""
        race_duration = 5.5  # hours
        schedule = self.calculator.generate_hourly_schedule(
            race_duration,
            60,
            24,
            350,  # carbs, fluid, sodium per hour
        )

        assert "carbs" in schedule
        assert "fluids" in schedule
        assert "sodium" in schedule

        # Should have 6 hours (ceil of 5.5)
        assert len(schedule["carbs"]) == 6
        assert len(schedule["fluids"]) == 6
        assert len(schedule["sodium"]) == 6

        # First hour should be reduced
        assert schedule["carbs"][0] < 60  # Reduced from target
        assert schedule["fluids"][0] < 24  # Reduced from target

        # Middle hours should be close to targets
        assert 50 <= schedule["carbs"][2] <= 60  # Should be near target
        assert 20 <= schedule["fluids"][2] <= 24  # Should be near target

    def test_environmental_risk_assessment(self):
        """Test environmental risk assessment"""
        hot_risks = self.calculator.assess_environmental_risk(self.hot_conditions)
        cool_risks = self.calculator.assess_environmental_risk(self.cool_conditions)

        assert "heat" in hot_risks
        assert "humidity" in hot_risks
        assert "heat" in cool_risks  # Always assessed

        # Hot conditions should have higher risk levels
        assert "HIGH" in hot_risks["heat"] or "MODERATE" in hot_risks["heat"]
        assert "LOW" in cool_risks["heat"]

    def test_heat_index_calculation(self):
        """Test heat index calculation helper method"""
        # Test various temperature/humidity combinations
        moderate_hi = self.calculator._calculate_heat_index(75, 50)
        hot_hi = self.calculator._calculate_heat_index(90, 70)

        assert moderate_hi >= 75
        assert hot_hi > moderate_hi
        assert hot_hi >= 90  # Should be at least the temperature

    def test_calculation_edge_cases(self):
        """Test edge cases and bounds checking"""
        # Very light athlete
        light_athlete = AthleteProfile(
            "Light", 150, 80, 9, "beginner", None, [], [], None, 100, 60, 20
        )

        # Extreme conditions
        extreme_hot = RaceConditions(105, 0, "none", "none", 90)
        extreme_cold = RaceConditions(35, 20, "headwind", "none", 20)

        # Should not crash and should return reasonable values
        hot_sweat = self.calculator.calculate_sweat_rate(light_athlete, extreme_hot)
        cold_sweat = self.calculator.calculate_sweat_rate(light_athlete, extreme_cold)

        assert 12 <= hot_sweat <= 50  # Within physiological bounds
        assert 12 <= cold_sweat <= 50
        assert hot_sweat > cold_sweat  # Hot should still be higher

    def test_very_long_race_schedule(self):
        """Test nutrition schedule for very long races"""
        # Test 8-hour race
        long_schedule = self.calculator.generate_hourly_schedule(8.0, 45, 20, 300)

        assert len(long_schedule["carbs"]) == 8

        # All hours should have some nutrition
        for hour_carbs in long_schedule["carbs"]:
            assert hour_carbs > 0

        # Total carbs should be reasonable for long race
        total_carbs = sum(long_schedule["carbs"])
        assert 200 <= total_carbs <= 500  # 8 hours * ~30-60g/hr range
