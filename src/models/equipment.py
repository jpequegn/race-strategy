"""
Equipment models for triathlon race strategy.

Defines data structures for equipment recommendations including bike setup,
swim gear, run equipment, and performance impact analysis.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class BikeSetup:
    """Bike configuration recommendations"""

    gearing: str  # "compact", "standard", "1x", "custom"
    gearing_rationale: str  # Why this gearing choice
    wheels: str  # "climbing", "aero", "all-around", "deep-section"
    wheel_rationale: str  # Why these wheels
    position: str  # "aggressive", "moderate", "comfort", "time-trial"
    position_rationale: str  # Position adjustment reasoning
    tire_pressure: Optional[str] = None  # Pressure recommendations
    accessories: List[str] = None  # Additional bike accessories


@dataclass
class SwimGear:
    """Swimming equipment recommendations"""

    wetsuit_decision: str  # "wetsuit", "no-wetsuit", "depends-on-temp"
    wetsuit_rationale: str  # Why wetsuit/no-wetsuit decision
    wetsuit_type: Optional[str] = None  # "full", "sleeveless", "shorty" if wetsuit
    goggles: str  # "clear", "tinted", "mirrored", "photochromic"
    goggle_rationale: str  # Why these goggles
    cap_strategy: Optional[str] = None  # Swimming cap considerations
    accessories: List[str] = None  # Additional swim accessories


@dataclass
class RunEquipment:
    """Running gear recommendations"""

    shoes: str  # "stability", "neutral", "minimal", "max-cushion"
    shoe_rationale: str  # Why this shoe category
    clothing: str  # Weather-appropriate clothing recommendations
    clothing_rationale: str  # Why this clothing choice
    accessories: List[str] = None  # Additional run accessories
    fuel_carrying: Optional[str] = None  # How to carry nutrition


@dataclass
class AccessoryRecommendations:
    """Race accessories and tools"""

    nutrition_storage: List[str]  # How to carry fuel and hydration
    tools_spares: List[str]  # Essential bike tools and spare parts
    electronics: List[str]  # GPS, power meter considerations
    other_gear: List[str] = None  # Other helpful accessories


@dataclass
class PerformanceImpact:
    """Expected performance benefits and costs"""

    time_savings_estimate: str  # Expected time savings from recommendations
    cost_analysis: str  # Cost vs benefit analysis
    priority_ranking: List[str]  # Most important to least important changes
    risk_assessment: str  # Risks of equipment choices
    alternatives: Optional[str] = None  # Alternative equipment options


@dataclass
class EquipmentRecommendations:
    """Complete equipment strategy for a race"""

    race_name: str
    athlete_name: str
    conditions_summary: str
    bike_setup: BikeSetup
    swim_gear: SwimGear
    run_equipment: RunEquipment
    accessories: AccessoryRecommendations
    performance_impact: PerformanceImpact
    
    # Meta information
    confidence_level: str = "high"  # "low", "medium", "high"
    last_updated: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class EquipmentItem:
    """Individual equipment item with specifications"""

    name: str
    category: str  # "bike", "swim", "run", "accessory"
    subcategory: str  # "wheels", "wetsuit", "shoes", etc.
    brand: Optional[str] = None
    model: Optional[str] = None
    weight_grams: Optional[int] = None
    cost_usd: Optional[int] = None
    performance_rating: Optional[float] = None  # 1.0-10.0 scale
    conditions_rating: Optional[str] = None  # Best conditions for this item
    athlete_suitability: Optional[str] = None  # What type of athlete benefits most
    pros: List[str] = None
    cons: List[str] = None
    specifications: Optional[str] = None  # Technical specifications