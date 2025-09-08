# tests/test_course_difficulty.py
"""
Comprehensive tests for the course difficulty calculator.
"""

import pytest

from src.models.course import CourseProfile, ClimbSegment
from src.utils.course_analyzer import DifficultyCalculator
from src.utils.course_loader import (
    load_alpe_dhuez_real,
    load_happy_valley_70_3_gps,
)


class TestDifficultyCalculator:
    """Test suite for DifficultyCalculator class."""

    @pytest.fixture
    def calculator(self):
        """Create a DifficultyCalculator instance."""
        return DifficultyCalculator()

    @pytest.fixture
    def flat_course(self):
        """Create a flat test course."""
        return CourseProfile(
            name="Flat Test Course",
            bike_distance_miles=56.0,
            bike_elevation_gain_ft=500,
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=100,
            key_climbs=[],
            technical_sections=[],
            altitude_ft=100,
        )

    @pytest.fixture
    def hilly_course(self):
        """Create a hilly test course."""
        climbs = [
            ClimbSegment(
                name="Hill 1",
                start_mile=10.0,
                length_miles=1.5,
                avg_grade=6.0,
                max_grade=10.0,
                elevation_gain_ft=400,
            ),
            ClimbSegment(
                name="Hill 2",
                start_mile=25.0,
                length_miles=2.0,
                avg_grade=5.0,
                max_grade=8.0,
                elevation_gain_ft=500,
            ),
            ClimbSegment(
                name="Hill 3",
                start_mile=40.0,
                length_miles=1.0,
                avg_grade=8.0,
                max_grade=12.0,
                elevation_gain_ft=350,
            ),
        ]
        return CourseProfile(
            name="Hilly Test Course",
            bike_distance_miles=56.0,
            bike_elevation_gain_ft=3000,
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=500,
            key_climbs=climbs,
            technical_sections=["Technical descent at mile 12 (-8% grade)"],
            altitude_ft=500,
        )

    @pytest.fixture
    def mountain_course(self):
        """Create a mountainous test course."""
        climbs = [
            ClimbSegment(
                name="Major Climb 1",
                start_mile=5.0,
                length_miles=5.0,
                avg_grade=8.0,
                max_grade=15.0,
                elevation_gain_ft=2000,
            ),
            ClimbSegment(
                name="Major Climb 2",
                start_mile=30.0,
                length_miles=8.0,
                avg_grade=7.0,
                max_grade=18.0,
                elevation_gain_ft=2500,
            ),
            ClimbSegment(
                name="Final Ascent",
                start_mile=50.0,
                length_miles=3.0,
                avg_grade=12.0,
                max_grade=20.0,
                elevation_gain_ft=1500,
            ),
        ]
        technical = [
            "Steep descent at mile 15 (-15% grade)",
            "Technical switchbacks at mile 35",
            "Narrow descent at mile 45 (-12% grade)",
        ]
        return CourseProfile(
            name="Mountain Test Course",
            bike_distance_miles=60.0,
            bike_elevation_gain_ft=8000,
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=1000,
            key_climbs=climbs,
            technical_sections=technical,
            altitude_ft=6000,
        )

    def test_elevation_intensity_calculation(
        self, calculator, flat_course, hilly_course, mountain_course
    ):
        """Test elevation intensity calculation."""
        # Flat course
        flat_intensity = calculator._calculate_elevation_intensity(flat_course)
        assert flat_intensity == pytest.approx(8.93, rel=0.1)  # 500/56

        # Hilly course
        hilly_intensity = calculator._calculate_elevation_intensity(hilly_course)
        assert hilly_intensity == pytest.approx(53.57, rel=0.1)  # 3000/56

        # Mountain course
        mountain_intensity = calculator._calculate_elevation_intensity(mountain_course)
        assert mountain_intensity == pytest.approx(133.33, rel=0.1)  # 8000/60

    def test_gradient_distribution_analysis(
        self, calculator, hilly_course, mountain_course
    ):
        """Test gradient distribution analysis."""
        # Hilly course
        hilly_stats = calculator._analyze_gradient_distribution(hilly_course)
        assert hilly_stats["avg"] > 0
        assert hilly_stats["max"] == 12.0
        assert "distribution" in hilly_stats

        # Mountain course
        mountain_stats = calculator._analyze_gradient_distribution(mountain_course)
        assert mountain_stats["max"] == 20.0
        assert mountain_stats["avg"] < mountain_stats["max"]

    def test_climb_clustering_analysis(self, calculator, hilly_course, mountain_course):
        """Test climb clustering score calculation."""
        # Hilly course (evenly distributed climbs)
        hilly_clustering = calculator._analyze_climb_clustering(hilly_course)
        assert 0 <= hilly_clustering <= 1

        # Mountain course (longer, more clustered climbs)
        mountain_clustering = calculator._analyze_climb_clustering(mountain_course)
        assert (
            mountain_clustering > hilly_clustering
        )  # Mountain climbs are more sustained

    def test_technical_difficulty_scoring(
        self, calculator, flat_course, mountain_course
    ):
        """Test technical difficulty scoring."""
        # Flat course (no technical sections)
        flat_technical = calculator._calculate_technical_difficulty(flat_course)
        assert flat_technical == 0

        # Mountain course (multiple technical sections)
        mountain_technical = calculator._calculate_technical_difficulty(mountain_course)
        assert mountain_technical > 0
        assert mountain_technical <= 1

    def test_crux_segment_identification(self, calculator, mountain_course):
        """Test identification of crux segments."""
        crux_segments = calculator._identify_crux_segments(mountain_course, top_n=2)

        assert len(crux_segments) <= 2
        if crux_segments:
            # First crux should have highest difficulty score
            assert (
                crux_segments[0]["difficulty_score"]
                >= crux_segments[-1]["difficulty_score"]
            )
            # Should include strategic importance
            assert "strategic_importance" in crux_segments[0]

    def test_overall_difficulty_rating(
        self, calculator, flat_course, hilly_course, mountain_course
    ):
        """Test overall difficulty rating calculation."""
        # Flat course should have low rating
        flat_metrics = calculator.calculate_difficulty(flat_course)
        assert 1 <= flat_metrics.overall_rating <= 3

        # Hilly course should have moderate rating
        hilly_metrics = calculator.calculate_difficulty(hilly_course)
        assert 3 <= hilly_metrics.overall_rating <= 6

        # Mountain course should have high rating
        mountain_metrics = calculator.calculate_difficulty(mountain_course)
        assert mountain_metrics.overall_rating >= 7
        assert mountain_metrics.overall_rating <= 10

    def test_difficulty_justification_generation(self, calculator, mountain_course):
        """Test generation of difficulty justification."""
        metrics = calculator.calculate_difficulty(mountain_course)

        assert metrics.difficulty_justification
        assert isinstance(metrics.difficulty_justification, str)
        assert len(metrics.difficulty_justification) > 20
        # Should mention difficulty level
        assert any(
            word in metrics.difficulty_justification.lower()
            for word in ["challenging", "difficult", "hard", "extreme"]
        )

    def test_strategic_insights_generation(self, calculator, mountain_course):
        """Test generation of strategic insights."""
        metrics = calculator.calculate_difficulty(mountain_course)

        assert metrics.strategic_insights
        assert isinstance(metrics.strategic_insights, list)
        assert len(metrics.strategic_insights) > 0
        # Should provide actionable advice
        for insight in metrics.strategic_insights:
            assert isinstance(insight, str)
            assert len(insight) > 10

    def test_course_comparison(self, calculator):
        """Test course comparison functionality."""
        # Create two different courses
        easy_course = CourseProfile(
            name="Easy Course",
            bike_distance_miles=40.0,
            bike_elevation_gain_ft=800,
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=200,
            key_climbs=[ClimbSegment("Small Hill", 10, 0.5, 3, 5, 100)],
            technical_sections=[],
            altitude_ft=500,
        )

        hard_course = CourseProfile(
            name="Hard Course",
            bike_distance_miles=56.0,
            bike_elevation_gain_ft=5000,
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=800,
            key_climbs=[
                ClimbSegment("Big Climb", 20, 5, 10, 18, 2000),
                ClimbSegment("Steep Wall", 40, 2, 12, 20, 1000),
            ],
            technical_sections=["Steep descent -15%"],
            altitude_ft=7000,
        )

        comparison = calculator.compare_courses(easy_course, hard_course)

        assert comparison["harder_course"] == "Hard Course"
        assert comparison["difficulty_difference"] < 0  # Easy course has lower rating
        assert "key_differences" in comparison
        assert len(comparison["key_differences"]) > 0

    def test_altitude_effects_on_difficulty(self, calculator):
        """Test that altitude affects difficulty rating."""
        # Course at sea level
        low_altitude_course = CourseProfile(
            name="Sea Level Course",
            bike_distance_miles=56.0,
            bike_elevation_gain_ft=2000,
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=400,
            key_climbs=[ClimbSegment("Hill", 20, 2, 6, 10, 500)],
            technical_sections=[],
            altitude_ft=100,
        )

        # Same course at high altitude
        high_altitude_course = CourseProfile(
            name="High Altitude Course",
            bike_distance_miles=56.0,
            bike_elevation_gain_ft=2000,
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=400,
            key_climbs=[ClimbSegment("Hill", 20, 2, 6, 10, 500)],
            technical_sections=[],
            altitude_ft=8000,
        )

        low_metrics = calculator.calculate_difficulty(low_altitude_course)
        high_metrics = calculator.calculate_difficulty(high_altitude_course)

        # High altitude course should have higher difficulty
        assert high_metrics.overall_rating > low_metrics.overall_rating

    def test_real_course_alpe_dhuez(self, calculator):
        """Test with real Alpe d'Huez course data."""
        try:
            course = load_alpe_dhuez_real()
            metrics = calculator.calculate_difficulty(course)

            # Alpe d'Huez should be rated as very difficult
            assert metrics.overall_rating >= 8
            assert metrics.elevation_intensity > 150  # Extreme elevation
            assert metrics.technical_difficulty > 0  # Has technical sections
            assert len(metrics.crux_segments) > 0
            assert any("Alpe" in seg["name"] for seg in metrics.crux_segments)

            # Should mention altitude in insights
            assert any(
                "altitude" in insight.lower() for insight in metrics.strategic_insights
            )
        except FileNotFoundError:
            pytest.skip("Alpe d'Huez course data not available")

    def test_real_course_happy_valley(self, calculator):
        """Test with real Happy Valley course data."""
        try:
            course = load_happy_valley_70_3_gps()
            metrics = calculator.calculate_difficulty(course)

            # Happy Valley should be rated as moderate
            assert 4 <= metrics.overall_rating <= 7
            assert metrics.elevation_intensity < 100  # Not extreme
            assert len(metrics.crux_segments) > 0

        except FileNotFoundError:
            pytest.skip("Happy Valley course data not available")

    def test_real_course_comparison(self, calculator):
        """Test comparison of real courses (Happy Valley vs Alpe d'Huez)."""
        try:
            happy_valley = load_happy_valley_70_3_gps()
            alpe_dhuez = load_alpe_dhuez_real()

            comparison = calculator.compare_courses(happy_valley, alpe_dhuez)

            # Alpe d'Huez should be harder
            assert comparison["harder_course"] == alpe_dhuez.name
            assert comparison["difficulty_difference"] < 0

            # Should identify key differences
            differences = comparison["key_differences"]
            assert any("altitude" in diff.lower() for diff in differences)
            assert any(
                "climbing" in diff.lower() or "elevation" in diff.lower()
                for diff in differences
            )

        except FileNotFoundError:
            pytest.skip("Course data not available")

    def test_empty_course_handling(self, calculator):
        """Test handling of course with minimal data."""
        empty_course = CourseProfile(
            name="Empty Course",
            bike_distance_miles=0,
            bike_elevation_gain_ft=0,
            swim_distance_miles=0,
            run_distance_miles=0,
            run_elevation_gain_ft=0,
            key_climbs=[],
            technical_sections=[],
        )

        metrics = calculator.calculate_difficulty(empty_course)

        # Should handle gracefully
        assert metrics.overall_rating == 1.0
        assert metrics.elevation_intensity == 0
        assert metrics.crux_segments == []
