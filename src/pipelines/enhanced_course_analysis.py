# src/pipelines/enhanced_course_analysis.py
"""
Enhanced course analysis pipeline integrating difficulty calculation
with AI-powered strategic insights.
"""

import dspy
from typing import Dict, List, Optional

from ..models.course import CourseProfile
from ..models.athlete import AthleteProfile
from ..utils.course_analyzer import DifficultyCalculator, DifficultyMetrics


class EnhancedCourseAnalyzer(dspy.Signature):
    """
    Analyze course difficulty metrics and provide strategic insights
    tailored to the specific challenges identified.
    """

    course_name: str = dspy.InputField(desc="Name of the course being analyzed")
    difficulty_rating: float = dspy.InputField(
        desc="Overall difficulty rating (1-10 scale)"
    )
    difficulty_justification: str = dspy.InputField(
        desc="Explanation of difficulty rating"
    )
    elevation_intensity: float = dspy.InputField(
        desc="Elevation gain per mile (ft/mile)"
    )
    crux_segments_description: str = dspy.InputField(
        desc="Description of the most challenging segments"
    )
    technical_difficulty: float = dspy.InputField(
        desc="Technical difficulty score (0-1)"
    )
    climb_clustering: float = dspy.InputField(
        desc="Climb clustering score (0=rolling, 1=sustained)"
    )

    enhanced_strategic_analysis: str = dspy.OutputField(
        desc="Comprehensive strategic analysis based on difficulty metrics"
    )
    training_recommendations: str = dspy.OutputField(
        desc="Specific training recommendations based on course challenges"
    )
    race_day_tactics: str = dspy.OutputField(
        desc="Tactical recommendations for race day execution"
    )


class CourseComparisonAnalyzer(dspy.Signature):
    """
    Compare two courses and provide insights on their relative challenges
    and how to adapt training and strategy between them.
    """

    course1_name: str = dspy.InputField(desc="Name of first course")
    course1_rating: float = dspy.InputField(desc="Difficulty rating of first course")
    course2_name: str = dspy.InputField(desc="Name of second course")
    course2_rating: float = dspy.InputField(desc="Difficulty rating of second course")
    key_differences: str = dspy.InputField(desc="Key differences between the courses")
    metrics_comparison: str = dspy.InputField(
        desc="Detailed metrics comparison between courses"
    )

    comparative_analysis: str = dspy.OutputField(
        desc="Detailed comparison of course challenges and characteristics"
    )
    adaptation_strategy: str = dspy.OutputField(
        desc="How to adapt training when switching between these courses"
    )
    course_selection_advice: str = dspy.OutputField(
        desc="Advice on which course suits different athlete types"
    )


class EnhancedCourseAnalysisPipeline:
    """
    Pipeline for enhanced course analysis combining algorithmic difficulty
    calculation with AI-powered strategic insights.
    """

    def __init__(self):
        """Initialize the pipeline with difficulty calculator and DSPy modules."""
        self.difficulty_calculator = DifficultyCalculator()
        self.course_analyzer = dspy.ChainOfThought(EnhancedCourseAnalyzer)
        self.comparison_analyzer = dspy.ChainOfThought(CourseComparisonAnalyzer)

    def analyze_course(
        self, course: CourseProfile, athlete: Optional[AthleteProfile] = None
    ) -> Dict:
        """
        Perform comprehensive course analysis with difficulty calculation
        and strategic insights.

        Args:
            course: CourseProfile to analyze
            athlete: Optional AthleteProfile for personalized insights

        Returns:
            Dictionary containing difficulty metrics and strategic analysis
        """
        # Step 1: Calculate objective difficulty metrics
        difficulty_metrics = self.difficulty_calculator.calculate_difficulty(course)

        # Step 2: Format crux segments for AI analysis
        crux_description = self._format_crux_segments(difficulty_metrics.crux_segments)

        # Step 3: Get AI-enhanced strategic analysis
        ai_analysis = self.course_analyzer(
            course_name=course.name,
            difficulty_rating=difficulty_metrics.overall_rating,
            difficulty_justification=difficulty_metrics.difficulty_justification,
            elevation_intensity=difficulty_metrics.elevation_intensity,
            crux_segments_description=crux_description,
            technical_difficulty=difficulty_metrics.technical_difficulty,
            climb_clustering=difficulty_metrics.climb_clustering_score,
        )

        # Step 4: Combine algorithmic and AI insights
        combined_insights = (
            difficulty_metrics.strategic_insights
            + self._parse_ai_insights(ai_analysis.enhanced_strategic_analysis)
        )

        # Step 5: Personalize if athlete profile provided
        if athlete:
            combined_insights = self._personalize_insights(
                combined_insights, athlete, difficulty_metrics
            )

        return {
            "course_name": course.name,
            "difficulty_metrics": {
                "overall_rating": difficulty_metrics.overall_rating,
                "elevation_intensity": difficulty_metrics.elevation_intensity,
                "avg_gradient": difficulty_metrics.avg_gradient,
                "max_gradient": difficulty_metrics.max_gradient,
                "gradient_variance": difficulty_metrics.gradient_variance,
                "climb_clustering": difficulty_metrics.climb_clustering_score,
                "technical_difficulty": difficulty_metrics.technical_difficulty,
            },
            "difficulty_justification": difficulty_metrics.difficulty_justification,
            "crux_segments": difficulty_metrics.crux_segments,
            "strategic_insights": combined_insights,
            "training_recommendations": ai_analysis.training_recommendations,
            "race_day_tactics": ai_analysis.race_day_tactics,
        }

    def compare_courses(self, course1: CourseProfile, course2: CourseProfile) -> Dict:
        """
        Compare two courses with comprehensive analysis.

        Args:
            course1: First CourseProfile
            course2: Second CourseProfile

        Returns:
            Dictionary with comparison results and strategic insights
        """
        # Step 1: Get algorithmic comparison
        comparison = self.difficulty_calculator.compare_courses(course1, course2)

        # Step 2: Calculate individual metrics
        metrics1 = self.difficulty_calculator.calculate_difficulty(course1)
        metrics2 = self.difficulty_calculator.calculate_difficulty(course2)

        # Step 3: Format comparison data for AI
        metrics_comparison_text = self._format_metrics_comparison(
            comparison["metrics_comparison"]
        )
        key_differences_text = "\n".join(comparison["key_differences"])

        # Step 4: Get AI-enhanced comparison analysis
        ai_comparison = self.comparison_analyzer(
            course1_name=course1.name,
            course1_rating=metrics1.overall_rating,
            course2_name=course2.name,
            course2_rating=metrics2.overall_rating,
            key_differences=key_differences_text,
            metrics_comparison=metrics_comparison_text,
        )

        return {
            "comparison_summary": {
                "course1": course1.name,
                "course2": course2.name,
                "difficulty_difference": comparison["difficulty_difference"],
                "harder_course": comparison["harder_course"],
            },
            "metrics_comparison": comparison["metrics_comparison"],
            "key_differences": comparison["key_differences"],
            "comparative_analysis": ai_comparison.comparative_analysis,
            "adaptation_strategy": ai_comparison.adaptation_strategy,
            "course_selection_advice": ai_comparison.course_selection_advice,
        }

    def identify_optimal_segments(self, course: CourseProfile) -> List[Dict]:
        """
        Identify optimal segments for different race strategies.

        Args:
            course: CourseProfile to analyze

        Returns:
            List of segment recommendations for different strategies
        """
        # Calculate difficulty metrics (not used directly but validates course)
        self.difficulty_calculator.calculate_difficulty(course)

        segments = []

        # Recovery segments (easy sections after hard climbs)
        for i, climb in enumerate(course.key_climbs):
            if climb.avg_grade < 3 and i > 0:
                prev_climb = course.key_climbs[i - 1]
                if prev_climb.avg_grade > 8:
                    segments.append(
                        {
                            "type": "recovery",
                            "start_mile": climb.start_mile,
                            "description": f"Recovery opportunity after {prev_climb.name}",
                            "strategy": "Active recovery, hydrate and fuel",
                        }
                    )

        # Attack segments (steep but short climbs)
        for climb in course.key_climbs:
            if climb.length_miles < 1 and climb.avg_grade > 8:
                segments.append(
                    {
                        "type": "attack",
                        "start_mile": climb.start_mile,
                        "description": f"{climb.name} - short, steep climb",
                        "strategy": "High-intensity effort to create separation",
                    }
                )

        # Rhythm segments (long, steady climbs)
        for climb in course.key_climbs:
            if climb.length_miles > 2 and 4 < climb.avg_grade < 8:
                segments.append(
                    {
                        "type": "rhythm",
                        "start_mile": climb.start_mile,
                        "description": f"{climb.name} - sustained climb",
                        "strategy": "Maintain steady threshold power",
                    }
                )

        return segments

    def _format_crux_segments(self, crux_segments: List[Dict]) -> str:
        """Format crux segments for AI analysis."""
        descriptions = []
        for i, segment in enumerate(crux_segments, 1):
            desc = (
                f"{i}. {segment['name']} at mile {segment['start_mile']:.1f}: "
                f"{segment['length_miles']:.1f} miles at {segment['avg_grade']:.1f}% "
                f"average grade (max {segment['max_grade']:.1f}%), "
                f"{segment['elevation_gain_ft']} ft gain. "
                f"Strategic importance: {segment['strategic_importance']}"
            )
            descriptions.append(desc)
        return "\n".join(descriptions)

    def _format_metrics_comparison(self, metrics_comp: Dict) -> str:
        """Format metrics comparison for AI analysis."""
        lines = []
        for metric, values in metrics_comp.items():
            metric_name = metric.replace("_", " ").title()
            values_str = ", ".join([f"{k}: {v}" for k, v in values.items()])
            lines.append(f"{metric_name}: {values_str}")
        return "\n".join(lines)

    def _parse_ai_insights(self, ai_text: str) -> List[str]:
        """Parse AI-generated insights into list format."""
        # Split by newlines or periods and filter empty strings
        insights = [
            insight.strip()
            for insight in ai_text.replace("\n", ". ").split(".")
            if insight.strip()
        ]
        return insights[:5]  # Limit to top 5 insights

    def _personalize_insights(
        self,
        insights: List[str],
        athlete: AthleteProfile,
        metrics: DifficultyMetrics,
    ) -> List[str]:
        """Personalize insights based on athlete profile."""
        personalized = insights.copy()

        # Add personalized recommendations based on athlete strengths
        if athlete.climbing_ability > 7 and metrics.climb_clustering_score > 0.6:
            personalized.insert(
                0,
                "Your strong climbing ability is well-suited for this course's sustained climbs",
            )
        elif athlete.climbing_ability < 5 and metrics.elevation_intensity > 100:
            personalized.insert(
                0,
                "Focus on improving climbing efficiency - this course demands strong climbing",
            )

        # FTP-based recommendations
        if athlete.ftp_watts > 0:
            watts_per_kg = athlete.ftp_watts / (athlete.weight_kg or 70)
            if watts_per_kg > 4 and metrics.overall_rating > 7:
                personalized.append(
                    "Your high power-to-weight ratio will be advantageous on this difficult course"
                )
            elif watts_per_kg < 3 and metrics.overall_rating > 5:
                personalized.append(
                    "Consider building FTP to better handle this course's demands"
                )

        return personalized
