# src/utils/course_analyzer.py
"""
Course difficulty analyzer for intelligent race strategy planning.

This module provides comprehensive analysis of course difficulty based on
GPS elevation data, identifying strategic segments and providing objective
difficulty ratings.
"""

from dataclasses import dataclass
from statistics import mean, stdev
from typing import Dict, List

from ..models.course import ClimbSegment, CourseProfile


@dataclass
class DifficultyMetrics:
    """Container for course difficulty metrics."""

    overall_rating: float  # 1-10 scale
    elevation_intensity: float  # ft/mile
    avg_gradient: float  # average gradient %
    max_gradient: float  # maximum gradient %
    gradient_variance: float  # gradient distribution spread
    climb_clustering_score: float  # 0-1 (0=evenly distributed, 1=highly clustered)
    technical_difficulty: float  # 0-1 based on steep gradients and descents
    crux_segments: List[Dict]  # most challenging segments
    difficulty_justification: str  # explanation of rating
    strategic_insights: List[str]  # race strategy recommendations


class DifficultyCalculator:
    """
    Intelligent course difficulty calculator that analyzes GPS elevation data
    to generate objective difficulty ratings and strategic insights.
    """

    # Thresholds for difficulty scoring
    GRADIENT_THRESHOLDS = {
        "easy": 3.0,  # < 3% is easy
        "moderate": 6.0,  # 3-6% is moderate
        "hard": 10.0,  # 6-10% is hard
        "extreme": 15.0,  # > 10% is extreme
    }

    ELEVATION_INTENSITY_THRESHOLDS = {
        "flat": 20,  # < 20 ft/mile
        "rolling": 50,  # 20-50 ft/mile
        "hilly": 100,  # 50-100 ft/mile
        "mountainous": 150,  # 100-150 ft/mile
        "extreme": 200,  # > 150 ft/mile
    }

    def calculate_difficulty(self, course: CourseProfile) -> DifficultyMetrics:
        """
        Calculate comprehensive difficulty metrics for a course.

        Args:
            course: CourseProfile object with elevation data

        Returns:
            DifficultyMetrics object with ratings and insights
        """
        # Calculate base metrics
        elevation_intensity = self._calculate_elevation_intensity(course)
        gradient_stats = self._analyze_gradient_distribution(course)
        climb_clustering = self._analyze_climb_clustering(course)
        technical_score = self._calculate_technical_difficulty(course)
        crux_segments = self._identify_crux_segments(course)

        # Calculate overall difficulty rating (1-10 scale)
        overall_rating = self._calculate_overall_rating(
            elevation_intensity,
            gradient_stats,
            climb_clustering,
            technical_score,
            course.altitude_ft,
        )

        # Generate justification
        justification = self._generate_difficulty_justification(
            overall_rating,
            elevation_intensity,
            gradient_stats,
            climb_clustering,
            technical_score,
            course.altitude_ft,
        )

        # Generate strategic insights
        insights = self._generate_strategic_insights(
            course, elevation_intensity, crux_segments, climb_clustering
        )

        return DifficultyMetrics(
            overall_rating=overall_rating,
            elevation_intensity=elevation_intensity,
            avg_gradient=gradient_stats["avg"],
            max_gradient=gradient_stats["max"],
            gradient_variance=gradient_stats["variance"],
            climb_clustering_score=climb_clustering,
            technical_difficulty=technical_score,
            crux_segments=crux_segments,
            difficulty_justification=justification,
            strategic_insights=insights,
        )

    def _calculate_elevation_intensity(self, course: CourseProfile) -> float:
        """Calculate elevation gain per mile."""
        total_distance = course.bike_distance_miles
        if total_distance == 0:
            return 0
        return course.bike_elevation_gain_ft / total_distance

    def _analyze_gradient_distribution(self, course: CourseProfile) -> Dict:
        """
        Analyze the distribution of gradients throughout the course.

        Returns dict with avg, max, variance, and distribution percentages.
        """
        gradients = []

        # Extract gradients from climbs
        for climb in course.key_climbs:
            gradients.append(climb.avg_grade)
            if climb.max_grade > 0:
                gradients.append(climb.max_grade)

        # Also analyze elevation profile if available
        if course.elevation_profile and len(course.elevation_profile) > 1:
            for i in range(1, len(course.elevation_profile)):
                point = course.elevation_profile[i]
                if point.gradient_percent is not None:
                    gradients.append(abs(point.gradient_percent))

        if not gradients:
            return {"avg": 0, "max": 0, "variance": 0, "distribution": {}}

        # Calculate statistics
        avg_gradient = mean(gradients)
        max_gradient = max(gradients)
        variance = stdev(gradients) if len(gradients) > 1 else 0

        # Categorize gradients
        distribution = {
            "easy": 0,
            "moderate": 0,
            "hard": 0,
            "extreme": 0,
        }

        for g in gradients:
            abs_g = abs(g)
            if abs_g < self.GRADIENT_THRESHOLDS["easy"]:
                distribution["easy"] += 1
            elif abs_g < self.GRADIENT_THRESHOLDS["moderate"]:
                distribution["moderate"] += 1
            elif abs_g < self.GRADIENT_THRESHOLDS["hard"]:
                distribution["hard"] += 1
            else:
                distribution["extreme"] += 1

        # Convert to percentages
        total = len(gradients)
        for key in distribution:
            distribution[key] = (distribution[key] / total * 100) if total > 0 else 0

        return {
            "avg": avg_gradient,
            "max": max_gradient,
            "variance": variance,
            "distribution": distribution,
        }

    def _analyze_climb_clustering(self, course: CourseProfile) -> float:
        """
        Analyze how climbs are distributed throughout the course.

        Returns a score 0-1 where:
        - 0 = evenly distributed (rolling)
        - 1 = highly clustered (long sustained climbs)
        """
        if not course.key_climbs:
            return 0

        # Calculate distances between climbs
        climb_positions = [climb.start_mile for climb in course.key_climbs]
        climb_positions.sort()

        if len(climb_positions) < 2:
            return 0

        # Calculate gaps between climbs
        gaps = []
        for i in range(1, len(climb_positions)):
            gaps.append(climb_positions[i] - climb_positions[i - 1])

        # Also consider climb lengths
        climb_lengths = [climb.length_miles for climb in course.key_climbs]
        max_climb_length = max(climb_lengths)

        # Calculate clustering score
        # High variance in gaps = more clustered
        gap_variance = stdev(gaps) if len(gaps) > 1 else 0
        avg_gap = mean(gaps) if gaps else 0

        # Normalize variance by average gap
        normalized_variance = gap_variance / avg_gap if avg_gap > 0 else 0

        # Factor in climb lengths (longer climbs = more sustained)
        length_factor = max_climb_length / course.bike_distance_miles

        # Combine factors (weighted average)
        clustering_score = min(1.0, (normalized_variance * 0.6) + (length_factor * 4))

        return clustering_score

    def _calculate_technical_difficulty(self, course: CourseProfile) -> float:
        """
        Calculate technical difficulty based on steep gradients and descents.

        Returns a score 0-1.
        """
        technical_score = 0
        factors = []

        # Analyze climbs for steep sections
        for climb in course.key_climbs:
            if climb.max_grade > 15:
                factors.append(min(1.0, climb.max_grade / 30))  # Normalize to 0-1
            if climb.avg_grade > 10:
                factors.append(min(1.0, climb.avg_grade / 20))

        # Analyze technical sections (descents, switchbacks, etc.)
        if course.technical_sections:
            for section in course.technical_sections:
                # Look for steep descents
                if "descent" in section.lower() or "%" in section:
                    # Try to extract gradient from description
                    import re

                    gradient_match = re.search(r"[-]?(\d+(?:\.\d+)?)\s*%", section)
                    if gradient_match:
                        gradient = abs(float(gradient_match.group(1)))
                        if gradient > 8:  # Steep descent
                            factors.append(min(1.0, gradient / 20))

                # Look for technical keywords
                technical_keywords = ["switchback", "technical", "narrow", "sharp"]
                if any(keyword in section.lower() for keyword in technical_keywords):
                    factors.append(0.5)  # Add moderate technical difficulty

        if factors:
            technical_score = mean(factors)

        return technical_score

    def _identify_crux_segments(
        self, course: CourseProfile, top_n: int = 3
    ) -> List[Dict]:
        """
        Identify the most challenging segments where races are won/lost.

        Args:
            course: CourseProfile object
            top_n: Number of crux segments to identify

        Returns:
            List of dictionaries describing crux segments
        """
        crux_candidates = []

        # Score each climb based on difficulty factors
        for climb in course.key_climbs:
            # Calculate difficulty score for this climb
            difficulty_score = 0

            # Factor 1: Gradient (weighted heavily)
            gradient_factor = (climb.avg_grade / 10) * 0.4
            max_gradient_factor = (climb.max_grade / 20) * 0.2
            difficulty_score += gradient_factor + max_gradient_factor

            # Factor 2: Length (longer climbs are harder)
            length_factor = (climb.length_miles / 3) * 0.2
            difficulty_score += length_factor

            # Factor 3: Elevation gain
            gain_factor = (climb.elevation_gain_ft / 1000) * 0.2
            difficulty_score += gain_factor

            # Factor 4: Position in race (later climbs are harder due to fatigue)
            position_factor = (climb.start_mile / course.bike_distance_miles) * 0.1
            difficulty_score += position_factor

            crux_candidates.append(
                {
                    "name": climb.name,
                    "start_mile": climb.start_mile,
                    "length_miles": climb.length_miles,
                    "avg_grade": climb.avg_grade,
                    "max_grade": climb.max_grade,
                    "elevation_gain_ft": climb.elevation_gain_ft,
                    "difficulty_score": min(1.0, difficulty_score),
                    "strategic_importance": self._assess_strategic_importance(
                        climb, course
                    ),
                }
            )

        # Sort by difficulty score and return top N
        crux_candidates.sort(key=lambda x: x["difficulty_score"], reverse=True)
        return crux_candidates[:top_n]

    def _assess_strategic_importance(
        self, climb: ClimbSegment, course: CourseProfile
    ) -> str:
        """Assess the strategic importance of a climb segment."""
        importance_factors = []

        # Check if it's a late-race climb
        if climb.start_mile > course.bike_distance_miles * 0.7:
            importance_factors.append("Late-race position increases importance")

        # Check if it's a very steep climb
        if climb.avg_grade > 10:
            importance_factors.append("Steep gradient creates selection")

        # Check if it's a long climb
        if climb.length_miles > 2:
            importance_factors.append("Sustained effort required")

        # Check if it's followed by technical descent
        if course.technical_sections:
            for section in course.technical_sections:
                if "descent" in section.lower():
                    # Check if descent is near this climb
                    import re

                    mile_match = re.search(r"mile\s+(\d+(?:\.\d+)?)", section)
                    if mile_match:
                        descent_mile = float(mile_match.group(1))
                        if (
                            abs(descent_mile - (climb.start_mile + climb.length_miles))
                            < 2
                        ):
                            importance_factors.append("Followed by technical descent")
                            break

        return "; ".join(importance_factors) if importance_factors else "Key segment"

    def _calculate_overall_rating(
        self,
        elevation_intensity: float,
        gradient_stats: Dict,
        climb_clustering: float,
        technical_score: float,
        altitude_ft: int,
    ) -> float:
        """
        Calculate overall difficulty rating on 1-10 scale.

        Weights different factors to produce final rating.
        """
        rating = 1.0  # Base rating

        # Factor 1: Elevation intensity (0-3 points)
        if elevation_intensity < self.ELEVATION_INTENSITY_THRESHOLDS["flat"]:
            intensity_points = 0.5
        elif elevation_intensity < self.ELEVATION_INTENSITY_THRESHOLDS["rolling"]:
            intensity_points = 1.0
        elif elevation_intensity < self.ELEVATION_INTENSITY_THRESHOLDS["hilly"]:
            intensity_points = 2.0
        elif elevation_intensity < self.ELEVATION_INTENSITY_THRESHOLDS["mountainous"]:
            intensity_points = 2.5
        else:
            intensity_points = 3.0
        rating += intensity_points

        # Factor 2: Average gradient (0-2 points)
        avg_gradient = gradient_stats["avg"]
        gradient_points = min(2.0, avg_gradient / 5)
        rating += gradient_points

        # Factor 3: Maximum gradient (0-1 point)
        max_gradient = gradient_stats["max"]
        max_gradient_points = min(1.0, max_gradient / 20)
        rating += max_gradient_points

        # Factor 4: Climb clustering (0-1 point)
        # Clustered climbs are harder (sustained efforts)
        rating += climb_clustering

        # Factor 5: Technical difficulty (0-1 point)
        rating += technical_score

        # Factor 6: Altitude effects (0-1 point)
        if altitude_ft > 5000:
            altitude_points = min(1.0, (altitude_ft - 5000) / 5000)
            rating += altitude_points

        # Cap at 10
        return min(10.0, round(rating, 1))

    def _generate_difficulty_justification(
        self,
        rating: float,
        elevation_intensity: float,
        gradient_stats: Dict,
        climb_clustering: float,
        technical_score: float,
        altitude_ft: int,
    ) -> str:
        """Generate human-readable justification for the difficulty rating."""
        justifications = []

        # Describe overall difficulty
        if rating <= 3:
            justifications.append("This is a relatively easy course")
        elif rating <= 5:
            justifications.append("This is a moderately challenging course")
        elif rating <= 7:
            justifications.append("This is a challenging course")
        else:
            justifications.append("This is an extremely difficult course")

        # Elevation intensity
        if elevation_intensity < self.ELEVATION_INTENSITY_THRESHOLDS["flat"]:
            justifications.append(
                f"with minimal elevation ({elevation_intensity:.0f} ft/mile)"
            )
        elif elevation_intensity < self.ELEVATION_INTENSITY_THRESHOLDS["rolling"]:
            justifications.append(
                f"with rolling terrain ({elevation_intensity:.0f} ft/mile)"
            )
        elif elevation_intensity < self.ELEVATION_INTENSITY_THRESHOLDS["hilly"]:
            justifications.append(
                f"with hilly terrain ({elevation_intensity:.0f} ft/mile)"
            )
        elif elevation_intensity < self.ELEVATION_INTENSITY_THRESHOLDS["mountainous"]:
            justifications.append(
                f"with mountainous terrain ({elevation_intensity:.0f} ft/mile)"
            )
        else:
            justifications.append(
                f"with extreme elevation ({elevation_intensity:.0f} ft/mile)"
            )

        # Gradients
        if gradient_stats["max"] > 15:
            justifications.append(
                f"including very steep sections up to {gradient_stats['max']:.1f}%"
            )
        elif gradient_stats["max"] > 10:
            justifications.append(
                f"with steep climbs up to {gradient_stats['max']:.1f}%"
            )

        # Climb pattern
        if climb_clustering > 0.7:
            justifications.append("featuring long, sustained climbs")
        elif climb_clustering < 0.3:
            justifications.append("with evenly distributed rolling hills")

        # Technical aspects
        if technical_score > 0.5:
            justifications.append("and significant technical challenges")

        # Altitude
        if altitude_ft > 5000:
            justifications.append(f"at high altitude ({altitude_ft:,} ft)")

        return ". ".join(justifications) + "."

    def _generate_strategic_insights(
        self,
        course: CourseProfile,
        elevation_intensity: float,
        crux_segments: List[Dict],
        climb_clustering: float,
    ) -> List[str]:
        """Generate strategic recommendations based on difficulty analysis."""
        insights = []

        # Pacing insights based on elevation intensity
        if elevation_intensity > self.ELEVATION_INTENSITY_THRESHOLDS["hilly"]:
            insights.append(
                "Conservative pacing essential - save energy for frequent climbs"
            )
        elif elevation_intensity > self.ELEVATION_INTENSITY_THRESHOLDS["rolling"]:
            insights.append("Maintain steady effort on rolling sections")

        # Climb distribution insights
        if climb_clustering > 0.7:
            insights.append(
                "Long climbs require sustained power - practice extended threshold efforts"
            )
        elif climb_clustering < 0.3:
            insights.append(
                "Frequent short climbs favor explosive power - train repeated accelerations"
            )

        # Crux segment insights
        if crux_segments:
            most_difficult = crux_segments[0]
            insights.append(
                f"Key selection point: {most_difficult['name']} at mile "
                f"{most_difficult['start_mile']:.1f} ({most_difficult['avg_grade']:.1f}% grade)"
            )

            # Late race crux warning
            late_crux = [
                s
                for s in crux_segments
                if s["start_mile"] > course.bike_distance_miles * 0.7
            ]
            if late_crux:
                insights.append(
                    f"Critical late-race climb at mile {late_crux[0]['start_mile']:.1f} "
                    "- conserve energy early"
                )

        # Technical insights
        if course.technical_sections:
            descent_count = sum(
                1 for s in course.technical_sections if "descent" in s.lower()
            )
            if descent_count > 3:
                insights.append(
                    f"{descent_count} technical descents - practice descending skills for time gains"
                )

        # Altitude insights
        if course.altitude_ft > 5000:
            insights.append(
                f"High altitude ({course.altitude_ft:,} ft) will reduce power output by ~10-15%"
            )
            insights.append("Arrive 2-3 days early for altitude acclimatization")

        # Nutrition insights based on difficulty
        if elevation_intensity > self.ELEVATION_INTENSITY_THRESHOLDS["hilly"]:
            insights.append(
                "High energy demands - increase carbohydrate intake to 90g/hour"
            )

        return insights

    def compare_courses(
        self, course1: CourseProfile, course2: CourseProfile
    ) -> Dict[str, any]:
        """
        Compare two courses objectively.

        Args:
            course1: First CourseProfile
            course2: Second CourseProfile

        Returns:
            Dictionary with comparison results
        """
        # Calculate metrics for both courses
        metrics1 = self.calculate_difficulty(course1)
        metrics2 = self.calculate_difficulty(course2)

        comparison = {
            "course1_name": course1.name,
            "course2_name": course2.name,
            "difficulty_difference": metrics1.overall_rating - metrics2.overall_rating,
            "harder_course": (
                course1.name
                if metrics1.overall_rating > metrics2.overall_rating
                else course2.name
            ),
            "metrics_comparison": {
                "overall_rating": {
                    course1.name: metrics1.overall_rating,
                    course2.name: metrics2.overall_rating,
                },
                "elevation_intensity": {
                    course1.name: round(metrics1.elevation_intensity, 1),
                    course2.name: round(metrics2.elevation_intensity, 1),
                },
                "max_gradient": {
                    course1.name: round(metrics1.max_gradient, 1),
                    course2.name: round(metrics2.max_gradient, 1),
                },
                "technical_difficulty": {
                    course1.name: round(metrics1.technical_difficulty, 2),
                    course2.name: round(metrics2.technical_difficulty, 2),
                },
                "climb_clustering": {
                    course1.name: round(metrics1.climb_clustering_score, 2),
                    course2.name: round(metrics2.climb_clustering_score, 2),
                },
            },
            "key_differences": self._identify_key_differences(
                course1, course2, metrics1, metrics2
            ),
        }

        return comparison

    def _identify_key_differences(
        self,
        course1: CourseProfile,
        course2: CourseProfile,
        metrics1: DifficultyMetrics,
        metrics2: DifficultyMetrics,
    ) -> List[str]:
        """Identify and describe key differences between courses."""
        differences = []

        # Overall difficulty
        diff_delta = abs(metrics1.overall_rating - metrics2.overall_rating)
        if diff_delta > 2:
            harder = (
                course1.name
                if metrics1.overall_rating > metrics2.overall_rating
                else course2.name
            )
            differences.append(
                f"{harder} is significantly more difficult ({diff_delta:.1f} points higher)"
            )
        elif diff_delta > 0.5:
            harder = (
                course1.name
                if metrics1.overall_rating > metrics2.overall_rating
                else course2.name
            )
            differences.append(f"{harder} is moderately more difficult")

        # Elevation intensity
        elev_diff = abs(metrics1.elevation_intensity - metrics2.elevation_intensity)
        if elev_diff > 50:
            hillier = (
                course1.name
                if metrics1.elevation_intensity > metrics2.elevation_intensity
                else course2.name
            )
            differences.append(
                f"{hillier} has much more climbing ({elev_diff:.0f} ft/mile more)"
            )

        # Climb pattern
        if abs(metrics1.climb_clustering_score - metrics2.climb_clustering_score) > 0.3:
            if metrics1.climb_clustering_score > metrics2.climb_clustering_score:
                differences.append(f"{course1.name} has longer sustained climbs")
                differences.append(f"{course2.name} has more rolling terrain")
            else:
                differences.append(f"{course2.name} has longer sustained climbs")
                differences.append(f"{course1.name} has more rolling terrain")

        # Technical difficulty
        if abs(metrics1.technical_difficulty - metrics2.technical_difficulty) > 0.2:
            more_technical = (
                course1.name
                if metrics1.technical_difficulty > metrics2.technical_difficulty
                else course2.name
            )
            differences.append(f"{more_technical} has more technical challenges")

        # Altitude
        alt_diff = abs(course1.altitude_ft - course2.altitude_ft)
        if alt_diff > 2000:
            higher = (
                course1.name
                if course1.altitude_ft > course2.altitude_ft
                else course2.name
            )
            differences.append(
                f"{higher} is at significantly higher altitude ({alt_diff:,} ft higher)"
            )

        return differences
