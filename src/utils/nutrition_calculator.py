"""
Nutrition calculation utilities for triathlon race strategy.

Provides evidence-based calculations for hydration, fueling, and electrolyte needs
based on athlete physiology, race duration, and environmental conditions.
"""

from typing import Tuple, Dict, List
import math
from ..models.athlete import AthleteProfile
from ..models.conditions import RaceConditions


class NutritionCalculator:
    """Calculate evidence-based nutrition requirements for triathlon racing"""

    # Sport nutrition constants based on research
    BASE_SWEAT_RATE_OZ_PER_HOUR = 20  # Baseline sweat rate per hour
    TEMP_SWEAT_MULTIPLIER = 0.015  # Additional sweat per degree F above 68
    HUMIDITY_SWEAT_MULTIPLIER = 0.002  # Additional sweat per % humidity above 40
    WEIGHT_SWEAT_FACTOR = 0.15  # Additional sweat per lb above 150lbs

    # Carbohydrate recommendations (grams per hour)
    MIN_CARBS_PER_HOUR = 30  # Minimum for races <2.5 hours
    STANDARD_CARBS_PER_HOUR = 60  # Standard for 2.5-3 hours
    HIGH_CARBS_PER_HOUR = 90  # High for 3+ hours with trained gut

    # Sodium recommendations (mg per hour)
    BASE_SODIUM_PER_HOUR = 300  # Base sodium replacement
    HIGH_SWEAT_SODIUM_BONUS = 200  # Additional for high sweat rates
    HOT_WEATHER_SODIUM_BONUS = 150  # Additional for hot conditions

    def __init__(self):
        """Initialize nutrition calculator with evidence-based constants"""
        pass

    def calculate_sweat_rate(
        self, athlete: AthleteProfile, conditions: RaceConditions
    ) -> float:
        """
        Calculate predicted sweat rate in oz per hour.

        Based on:
        - Athlete weight (heavier athletes typically sweat more)
        - Temperature (higher temps increase sweat rate)
        - Humidity (higher humidity impairs cooling)
        - Individual variation

        Args:
            athlete: Athlete profile with weight
            conditions: Race conditions with temp and humidity

        Returns:
            Predicted sweat rate in oz per hour
        """
        base_rate = self.BASE_SWEAT_RATE_OZ_PER_HOUR

        # Weight adjustment (heavier athletes sweat more)
        weight_diff = athlete.weight_lbs - 150  # Reference weight
        weight_adjustment = weight_diff * self.WEIGHT_SWEAT_FACTOR

        # Temperature adjustment (more sweat in heat)
        temp_diff = max(0, conditions.temperature_f - 68)  # Neutral temperature
        temp_adjustment = temp_diff * self.TEMP_SWEAT_MULTIPLIER

        # Humidity adjustment (impairs evaporative cooling)
        humidity_diff = max(0, conditions.humidity_percent - 40)  # Comfortable humidity
        humidity_adjustment = humidity_diff * self.HUMIDITY_SWEAT_MULTIPLIER

        total_sweat_rate = (
            base_rate + weight_adjustment + temp_adjustment + humidity_adjustment
        )

        # Cap at reasonable physiological limits
        return min(max(total_sweat_rate, 12), 50)  # 12-50 oz/hr range

    def calculate_carb_needs(
        self, race_duration_hours: float, intensity: str = "moderate"
    ) -> int:
        """
        Calculate carbohydrate needs per hour based on race duration and intensity.

        Based on current sports nutrition guidelines:
        - <2.5 hours: 30-60g/hr
        - 2.5-3 hours: 60g/hr
        - >3 hours: 60-90g/hr (with trained gut)

        Args:
            race_duration_hours: Expected race duration in hours
            intensity: "low", "moderate", "high"

        Returns:
            Recommended carbs per hour in grams
        """
        if race_duration_hours < 2.5:
            base_carbs = self.MIN_CARBS_PER_HOUR
            if intensity == "high":
                base_carbs = 50
        elif race_duration_hours < 3.0:
            base_carbs = self.STANDARD_CARBS_PER_HOUR
        else:
            base_carbs = self.STANDARD_CARBS_PER_HOUR
            if intensity == "high":
                base_carbs = self.HIGH_CARBS_PER_HOUR

        return base_carbs

    def calculate_sodium_needs(
        self,
        sweat_rate_oz_per_hour: float,
        conditions: RaceConditions,
        athlete: AthleteProfile,
    ) -> int:
        """
        Calculate sodium needs per hour in mg.

        Based on:
        - Baseline sodium loss rate
        - Sweat rate (higher sweat = more sodium loss)
        - Temperature (heat increases sodium needs)
        - Individual factors

        Args:
            sweat_rate_oz_per_hour: Calculated sweat rate
            conditions: Race conditions
            athlete: Athlete profile

        Returns:
            Sodium needs per hour in mg
        """
        base_sodium = self.BASE_SODIUM_PER_HOUR

        # High sweat rate bonus
        if sweat_rate_oz_per_hour > 30:
            base_sodium += self.HIGH_SWEAT_SODIUM_BONUS

        # Hot weather bonus
        if conditions.temperature_f > 80:
            base_sodium += self.HOT_WEATHER_SODIUM_BONUS

        # Cap at safe physiological limits
        return min(base_sodium, 800)  # Max ~800mg/hr for safety

    def calculate_fluid_replacement(
        self, sweat_rate_oz_per_hour: float
    ) -> Tuple[int, float]:
        """
        Calculate fluid replacement strategy.

        General guideline is to replace 75-100% of sweat losses.
        Higher replacement for shorter races, lower for longer races.

        Args:
            sweat_rate_oz_per_hour: Calculated sweat rate

        Returns:
            Tuple of (fluid_oz_per_hour, replacement_percentage)
        """
        # Replace 80-85% of sweat losses (prevents overhydration)
        replacement_percentage = 82.5
        fluid_per_hour = int(sweat_rate_oz_per_hour * (replacement_percentage / 100))

        # Practical limits for gastric emptying
        fluid_per_hour = min(max(fluid_per_hour, 12), 32)  # 12-32 oz/hr

        return fluid_per_hour, replacement_percentage

    def generate_hourly_schedule(
        self,
        race_duration_hours: float,
        carbs_per_hour: int,
        fluid_per_hour: int,
        sodium_per_hour: int,
    ) -> Dict[str, List[int]]:
        """
        Generate hour-by-hour nutrition targets.

        Accounts for:
        - Lower intake first hour (race start nerves/settling)
        - Consistent intake middle hours
        - Potential reduction final hour (close to finish)

        Args:
            race_duration_hours: Race duration in hours
            carbs_per_hour: Target carbs per hour
            fluid_per_hour: Target fluid per hour
            sodium_per_hour: Target sodium per hour

        Returns:
            Dict with hourly targets for each nutrient
        """
        num_hours = int(math.ceil(race_duration_hours))

        carb_schedule = []
        fluid_schedule = []
        sodium_schedule = []

        for hour in range(num_hours):
            # First hour: reduce intake due to race start
            if hour == 0:
                carb_hour = int(carbs_per_hour * 0.7)
                fluid_hour = int(fluid_per_hour * 0.8)
                sodium_hour = int(sodium_per_hour * 0.8)
            # Final partial hour: reduce if close to finish
            elif hour == num_hours - 1 and (race_duration_hours - hour) < 0.75:
                partial_hour = race_duration_hours - hour
                carb_hour = int(carbs_per_hour * partial_hour * 0.8)
                fluid_hour = int(fluid_per_hour * partial_hour)
                sodium_hour = int(sodium_per_hour * partial_hour)
            # Middle hours: full targets
            else:
                carb_hour = carbs_per_hour
                fluid_hour = fluid_per_hour
                sodium_hour = sodium_per_hour

            carb_schedule.append(carb_hour)
            fluid_schedule.append(fluid_hour)
            sodium_schedule.append(sodium_hour)

        return {
            "carbs": carb_schedule,
            "fluids": fluid_schedule,
            "sodium": sodium_schedule,
        }

    def assess_environmental_risk(self, conditions: RaceConditions) -> Dict[str, str]:
        """
        Assess environmental risks that affect nutrition strategy.

        Args:
            conditions: Race day conditions

        Returns:
            Dict of risk categories and recommendations
        """
        risks = {}

        # Heat risk assessment
        heat_index = self._calculate_heat_index(
            conditions.temperature_f, conditions.humidity_percent
        )
        if heat_index > 90:
            risks["heat"] = "HIGH - Increase fluid/sodium, pre-cool, slow early pace"
        elif heat_index > 80:
            risks["heat"] = "MODERATE - Increase hydration, monitor early"
        else:
            risks["heat"] = "LOW - Standard hydration protocol"

        # Humidity risk
        if conditions.humidity_percent > 80:
            risks["humidity"] = (
                "HIGH - Sweat won't evaporate efficiently, increase fluid"
            )
        elif conditions.humidity_percent > 60:
            risks["humidity"] = "MODERATE - Monitor sweat rate"
        else:
            risks["humidity"] = "LOW - Normal evaporative cooling"

        # Cold weather considerations
        if conditions.temperature_f < 50:
            risks["cold"] = (
                "Consider reduced fluid needs, warm fluids, maintain calorie intake"
            )

        return risks

    def _calculate_heat_index(self, temp_f: int, humidity: int) -> float:
        """Calculate apparent temperature accounting for humidity"""
        if temp_f < 80:
            return temp_f

        # Simplified heat index calculation
        hi = 0.5 * (temp_f + 61.0 + ((temp_f - 68.0) * 1.2) + (humidity * 0.094))

        if hi > 80:
            # More accurate formula for high temps
            hi = (
                -42.379
                + 2.04901523 * temp_f
                + 10.14333127 * humidity
                - 0.22475541 * temp_f * humidity
                - 0.00683783 * temp_f * temp_f
                - 0.05481717 * humidity * humidity
                + 0.00122874 * temp_f * temp_f * humidity
                + 0.00085282 * temp_f * humidity * humidity
                - 0.00000199 * temp_f * temp_f * humidity * humidity
            )

        return hi
