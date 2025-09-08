from dataclasses import dataclass
from typing import List, Optional


@dataclass
class NutritionItem:
    """Individual nutrition item with timing and quantities"""

    time_hours: float  # Race time in hours when to consume
    item_type: str  # "fluid", "gel", "bar", "electrolyte", "food"
    product_name: str  # Specific product recommendation
    quantity: str  # Amount to consume (e.g., "16 oz", "1 gel", "half bar")
    calories: int  # Caloric content
    carbs_g: int  # Carbohydrate content in grams
    sodium_mg: int  # Sodium content in milligrams
    notes: Optional[str] = None  # Special instructions or alternatives


@dataclass
class HydrationPlan:
    """Comprehensive hydration strategy for race day"""

    total_fluid_oz: int  # Total fluid intake recommendation
    hourly_targets: List[int]  # Fluid intake per hour in oz
    items: List[NutritionItem]  # Specific hydration items with timing
    sweat_rate_oz_per_hour: float  # Calculated sweat rate
    replacement_percentage: int  # Percentage of sweat loss to replace (usually 75-100%)
    hot_weather_adjustments: Optional[str] = None  # Adjustments for heat
    cool_weather_adjustments: Optional[str] = None  # Adjustments for cool conditions


@dataclass
class FuelingSchedule:
    """Race fueling plan with carbohydrate and calorie timing"""

    target_carbs_per_hour: int  # Target carb intake per hour in grams
    total_calories: int  # Total calories for entire race
    items: List[NutritionItem]  # Specific fueling items with timing
    pre_race_meal: Optional[str] = None  # Pre-race meal recommendations
    transition_nutrition: List[str] = None  # T1/T2 specific items
    late_race_strategy: Optional[str] = None  # Adjustments for final portion


@dataclass
class ElectrolyteStrategy:
    """Electrolyte replacement plan based on conditions and duration"""

    total_sodium_mg: int  # Total sodium replacement for race
    hourly_sodium_targets: List[int]  # Sodium per hour in mg
    items: List[NutritionItem]  # Specific electrolyte items
    cramping_prevention: Optional[str] = None  # Anti-cramping strategy
    heat_adaptations: Optional[str] = None  # Hot weather electrolyte needs
    individual_adjustments: Optional[str] = None  # Athlete-specific needs


@dataclass
class ContingencyNutrition:
    """Backup nutrition plan if primary strategy fails"""

    plan_b_items: List[str]  # Alternative products available on course
    gi_distress_protocol: str  # What to do if experiencing stomach issues
    bonk_recovery_items: List[str]  # Emergency carbs for energy crashes
    cramping_remedies: List[str]  # Emergency electrolyte options
    aid_station_strategy: str  # How to use race-provided nutrition


@dataclass
class NutritionPlan:
    """Complete race nutrition strategy"""

    race_duration_hours: float  # Predicted race duration
    athlete_weight_lbs: float  # Athlete weight for calculations
    conditions_summary: str  # Environmental conditions affecting strategy

    hydration_plan: HydrationPlan
    fueling_schedule: FuelingSchedule
    electrolyte_strategy: ElectrolyteStrategy
    contingency_nutrition: ContingencyNutrition

    # Integration points
    pacing_integration: Optional[str] = None  # How nutrition aligns with pacing
    timing_with_course: Optional[str] = None  # Course-specific timing considerations
    personalization_notes: Optional[str] = None  # Athlete-specific customizations

    # Validation and compliance
    sports_nutrition_compliance: bool = True  # Follows best practices
    evidence_basis: Optional[str] = None  # Scientific rationale for recommendations
