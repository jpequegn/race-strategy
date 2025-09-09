"""
Unit tests for Enhanced DSPy Course Analysis (Issue #13)
Tests the enhanced DSPy signatures and pipeline integration with DifficultyCalculator
"""

from unittest.mock import MagicMock, Mock, patch

import dspy
import pytest

from src.models.athlete import AthleteProfile
from src.models.conditions import RaceConditions
from src.models.course import ClimbSegment, CourseProfile
from src.pipelines.core_strategy import RaceStrategyPipeline
from src.pipelines.signatures import EnhancedCourseAnalyzer, SegmentAnalyzer


class TestEnhancedCourseAnalyzer:
    """Test suite for EnhancedCourseAnalyzer signature"""

    def test_signature_has_required_fields(self):
        """Test that EnhancedCourseAnalyzer has all required input/output fields"""
        signature = EnhancedCourseAnalyzer

        # Check field names using model_fields (Pydantic v2)
        field_names = list(signature.model_fields.keys())

        # Should have expected input fields
        expected_inputs = [
            "course_name",
            "course_profile",
            "elevation_data",
            "difficulty_metrics",
            "crux_segments",
        ]
        for input_field in expected_inputs:
            assert input_field in field_names, f"Missing input field: {input_field}"

        # Should have at least 5 input fields
        assert len([f for f in field_names if f in expected_inputs]) >= 5

    def test_signature_output_fields(self):
        """Test that EnhancedCourseAnalyzer has enhanced output fields"""
        signature = EnhancedCourseAnalyzer

        # Check that we have enhanced outputs beyond basic CourseAnalyzer
        field_names = list(signature.model_fields.keys())

        # Should have strategic outputs
        expected_outputs = [
            "strategic_analysis",
            "segment_analysis",
            "power_pacing_plan",
            "tactical_insights",
            "difficulty_justification",
        ]

        for output in expected_outputs:
            assert output in field_names, f"Missing expected output field: {output}"


class TestSegmentAnalyzer:
    """Test suite for SegmentAnalyzer signature"""

    def test_segment_analyzer_fields(self):
        """Test that SegmentAnalyzer has segment-specific fields"""
        signature = SegmentAnalyzer
        field_names = list(signature.model_fields.keys())

        # Input fields for segment analysis
        expected_inputs = ["segment_data", "segment_position", "athlete_context"]
        for input_field in expected_inputs:
            assert input_field in field_names, f"Missing input field: {input_field}"

        # Output fields for segment recommendations
        expected_outputs = [
            "power_recommendation",
            "tactical_approach",
            "risk_mitigation",
            "success_metrics",
        ]
        for output_field in expected_outputs:
            assert output_field in field_names, f"Missing output field: {output_field}"


class TestRaceStrategyPipelineEnhanced:
    """Test suite for enhanced RaceStrategyPipeline"""

    @pytest.fixture
    def mock_difficulty_calculator(self):
        """Create a mock DifficultyCalculator"""
        mock_calc = Mock()
        mock_metrics = Mock()
        mock_metrics.overall_rating = 7.5
        mock_metrics.elevation_intensity = 125.0
        mock_metrics.avg_gradient = 3.5
        mock_metrics.max_gradient = 12.0
        mock_metrics.gradient_variance = 2.1
        mock_metrics.climb_clustering_score = 0.6
        mock_metrics.technical_difficulty = 0.4
        mock_metrics.difficulty_justification = (
            "Challenging course with sustained climbs"
        )
        mock_metrics.crux_segments = [
            {
                "name": "Test Climb 1",
                "start_mile": 15.0,
                "length_miles": 2.5,
                "avg_grade": 8.0,
                "max_grade": 12.0,
                "elevation_gain_ft": 600,
                "difficulty_score": 0.85,
                "strategic_importance": "Critical climb that determines race outcome",
            },
            {
                "name": "Test Climb 2",
                "start_mile": 35.0,
                "length_miles": 1.8,
                "avg_grade": 6.5,
                "max_grade": 10.0,
                "elevation_gain_ft": 450,
                "difficulty_score": 0.72,
                "strategic_importance": "Late race challenge requiring energy management",
            },
        ]
        mock_calc.calculate_difficulty.return_value = mock_metrics
        return mock_calc

    @pytest.fixture
    def sample_course(self):
        """Create a sample course for testing"""
        return CourseProfile(
            name="Test Course Enhanced",
            bike_distance_miles=56.0,
            bike_elevation_gain_ft=4200,
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=800,
            key_climbs=[
                ClimbSegment("Test Climb 1", 15.0, 2.5, 8.0, 12.0, 600),
                ClimbSegment("Test Climb 2", 35.0, 1.8, 6.5, 10.0, 450),
            ],
            technical_sections=["Technical descent at mile 20"],
            altitude_ft=2000,
        )

    @pytest.fixture
    def sample_athlete(self):
        """Create a sample athlete for testing"""
        return AthleteProfile(
            name="Test Athlete Enhanced",
            ftp_watts=270,
            swim_pace_per_100m=88,
            run_threshold_pace=7.2,
            experience_level="advanced",
            previous_70_3_time="5:25:00",
            strengths=["climbing", "bike"],
            limiters=["swim_technique"],
            target_finish_time="5:15:00",
            age=30,
            weight_lbs=150,
        )

    @pytest.fixture
    def sample_conditions(self):
        """Create sample race conditions"""
        return RaceConditions(
            temperature_f=78,
            wind_speed_mph=10,
            wind_direction="variable",
            precipitation="none",
            humidity_percent=70,
        )

    @patch("src.pipelines.core_strategy.DifficultyCalculator")
    def test_pipeline_initialization(self, mock_diff_calc_class):
        """Test that enhanced pipeline initializes with DifficultyCalculator"""
        pipeline = RaceStrategyPipeline()

        # Should have initialized DifficultyCalculator
        mock_diff_calc_class.assert_called_once()

        # Should have enhanced DSPy modules
        assert hasattr(pipeline, "difficulty_calculator")
        assert hasattr(pipeline, "enhanced_course_analyzer")
        assert hasattr(pipeline, "segment_analyzer")

    @patch("src.pipelines.core_strategy.dspy")
    @patch("src.pipelines.core_strategy.DifficultyCalculator")
    def test_enhanced_pipeline_structure(self, mock_diff_calc_class, mock_dspy):
        """Test that pipeline has enhanced structure with new components"""
        pipeline = RaceStrategyPipeline()

        # Should have created ChainOfThought modules for enhanced signatures
        assert (
            mock_dspy.ChainOfThought.call_count >= 6
        )  # All DSPy modules including enhanced ones

    def test_format_elevation_data(self, sample_course):
        """Test elevation data formatting for DSPy input"""
        pipeline = RaceStrategyPipeline()
        elevation_data = pipeline._format_elevation_data(sample_course)

        assert "Mile" in elevation_data
        assert "gradient" in elevation_data
        assert "%" in elevation_data

        # Should contain mile-by-mile breakdown
        lines = elevation_data.split("\n")
        assert len(lines) > 10  # Should have multiple mile entries

    def test_format_difficulty_metrics(self, mock_difficulty_calculator):
        """Test difficulty metrics formatting"""
        pipeline = RaceStrategyPipeline()
        mock_metrics = mock_difficulty_calculator.calculate_difficulty.return_value

        formatted = pipeline._format_difficulty_metrics(mock_metrics)

        assert "Overall Difficulty Rating: 7.5/10" in formatted
        assert "Elevation Intensity: 125.0 ft/mile" in formatted
        assert "Challenging course with sustained climbs" in formatted

    def test_format_crux_segments(self, mock_difficulty_calculator):
        """Test crux segments formatting"""
        pipeline = RaceStrategyPipeline()
        mock_metrics = mock_difficulty_calculator.calculate_difficulty.return_value
        crux_segments = mock_metrics.crux_segments

        formatted = pipeline._format_crux_segments(crux_segments)

        assert "Test Climb 1" in formatted
        assert "Test Climb 2" in formatted
        assert "Mile 15.0" in formatted
        assert "Mile 35.0" in formatted
        assert "Strategic Importance" in formatted
        assert "Difficulty Score" in formatted

    def test_format_segment_data(self, mock_difficulty_calculator):
        """Test individual segment data formatting"""
        pipeline = RaceStrategyPipeline()
        sample_course = Mock()
        sample_course.bike_distance_miles = 56.0

        mock_metrics = mock_difficulty_calculator.calculate_difficulty.return_value
        segment = mock_metrics.crux_segments[0]  # First crux segment

        formatted = pipeline._format_segment_data(segment, sample_course)

        assert "Test Climb 1" in formatted
        assert "Mile 15.0 - 17.5" in formatted  # start to end mile
        assert "2.5 miles" in formatted
        assert "8.0%" in formatted  # More flexible matching
        assert "12.0%" in formatted
        assert "600 feet" in formatted

    def test_format_segment_position(self, mock_difficulty_calculator):
        """Test segment position context formatting"""
        pipeline = RaceStrategyPipeline()
        sample_course = Mock()
        sample_course.bike_distance_miles = 56.0

        mock_metrics = mock_difficulty_calculator.calculate_difficulty.return_value
        segment = mock_metrics.crux_segments[0]  # Mile 15.0 segment

        formatted = pipeline._format_segment_position(segment, sample_course)

        assert "Race Position" in formatted
        assert "quarter" in formatted.lower()  # Should mention quarters
        assert "15.0" in formatted and "56" in formatted  # Should have mile info
        assert "Fatigue Context" in formatted

    def test_format_athlete_for_segment(
        self, sample_athlete, mock_difficulty_calculator
    ):
        """Test athlete context formatting for segment"""
        pipeline = RaceStrategyPipeline()
        mock_metrics = mock_difficulty_calculator.calculate_difficulty.return_value
        segment = mock_metrics.crux_segments[0]

        formatted = pipeline._format_athlete_for_segment(sample_athlete, segment)

        assert sample_athlete.name in formatted
        assert "270W" in formatted
        assert "W/kg" in formatted  # Should calculate watts per kg
        assert "climbing" in formatted.lower()  # Should mention climbing ability
        assert (
            "High" in formatted or "Moderate" in formatted
        )  # Should have challenge level

    @patch("src.pipelines.core_strategy.dspy.ChainOfThought")
    def test_generate_strategy_calls_enhanced_modules(
        self,
        mock_cot,
        sample_course,
        sample_athlete,
        sample_conditions,
        mock_difficulty_calculator,
    ):
        """Test that generate_strategy calls enhanced DSPy modules"""
        # Mock the ChainOfThought instances
        mock_enhanced_analyzer = Mock()
        mock_enhanced_analyzer.return_value = Mock(
            strategic_analysis="Test analysis",
            segment_analysis="Test segment analysis",
            power_pacing_plan="Test power plan",
            tactical_insights="Test insights",
            difficulty_justification="Test justification",
        )

        mock_segment_analyzer = Mock()
        mock_segment_analyzer.return_value = Mock(
            power_recommendation="Test power rec",
            tactical_approach="Test tactics",
            risk_mitigation="Test risks",
            success_metrics="Test metrics",
        )

        mock_athlete_assessor = Mock()
        mock_athlete_assessor.return_value = Mock(
            strengths_vs_course="Test strengths",
            risk_areas="Test risks",
            power_targets="Test targets",
        )

        mock_pacing_strategist = Mock()
        mock_pacing_strategist.return_value = Mock(
            swim_strategy="Test swim",
            bike_strategy="Test bike",
            run_strategy="Test run",
        )

        mock_risk_assessor = Mock()
        mock_risk_assessor.return_value = Mock(mitigation_plan="Test mitigation")

        mock_optimizer = Mock()
        mock_optimizer.return_value = Mock(
            final_strategy="Test final strategy",
            time_prediction="Test time",
            success_probability="Test probability",
            key_success_factors="Test factors",
        )

        # Set up the ChainOfThought mock to return our mocked modules
        mock_cot.side_effect = [
            mock_enhanced_analyzer,
            mock_segment_analyzer,
            mock_athlete_assessor,
            mock_pacing_strategist,
            mock_risk_assessor,
            mock_optimizer,
        ]

        with patch(
            "src.pipelines.core_strategy.DifficultyCalculator",
            return_value=mock_difficulty_calculator,
        ):
            pipeline = RaceStrategyPipeline()
            results = pipeline.generate_strategy(
                sample_course, sample_athlete, sample_conditions
            )

        # Should call DifficultyCalculator
        mock_difficulty_calculator.calculate_difficulty.assert_called_once_with(
            sample_course
        )

        # Should call enhanced course analyzer
        mock_enhanced_analyzer.assert_called_once()
        call_kwargs = mock_enhanced_analyzer.call_args.kwargs
        assert "course_name" in call_kwargs
        assert "course_profile" in call_kwargs
        assert "elevation_data" in call_kwargs
        assert "difficulty_metrics" in call_kwargs
        assert "crux_segments" in call_kwargs

        # Should call segment analyzer for crux segments
        assert mock_segment_analyzer.call_count >= 1  # At least one crux segment

        # Results should include enhanced data
        assert "difficulty_metrics" in results
        assert "enhanced_course_analysis" in results
        assert "segment_analyses" in results


class TestEnhancedPipelineIntegration:
    """Integration tests for enhanced pipeline components"""

    @pytest.fixture
    def mock_difficulty_calculator(self):
        """Create a mock DifficultyCalculator for integration tests"""
        mock_calc = Mock()
        mock_metrics = Mock()
        mock_metrics.overall_rating = 6.8
        mock_metrics.elevation_intensity = 110.0
        mock_metrics.avg_gradient = 3.2
        mock_metrics.max_gradient = 11.5
        mock_metrics.gradient_variance = 1.8
        mock_metrics.climb_clustering_score = 0.55
        mock_metrics.technical_difficulty = 0.35
        mock_metrics.difficulty_justification = "Moderately challenging course"
        mock_metrics.crux_segments = [
            {
                "name": "Integration Climb",
                "start_mile": 20.0,
                "length_miles": 3.0,
                "avg_grade": 7.5,
                "max_grade": 11.5,
                "elevation_gain_ft": 750,
                "difficulty_score": 0.78,
                "strategic_importance": "Key climb for integration testing",
            }
        ]
        mock_calc.calculate_difficulty.return_value = mock_metrics
        return mock_calc

    @pytest.fixture
    def integration_course(self):
        """Create a realistic course for integration testing"""
        return CourseProfile(
            name="Integration Test Course",
            bike_distance_miles=56.0,
            bike_elevation_gain_ft=3800,
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=650,
            key_climbs=[
                ClimbSegment("Early Hills", 8.0, 3.0, 4.5, 7.0, 500),
                ClimbSegment("Major Climb", 28.0, 4.5, 7.2, 11.5, 1200),
                ClimbSegment("Final Challenge", 48.0, 2.2, 5.8, 9.2, 450),
            ],
            technical_sections=["Steep descent after major climb", "Technical corners"],
            altitude_ft=1500,
        )

    def test_enhanced_pipeline_data_flow(
        self, integration_course, mock_difficulty_calculator
    ):
        """Test that data flows correctly through enhanced pipeline"""
        with patch(
            "src.pipelines.core_strategy.DifficultyCalculator",
            return_value=mock_difficulty_calculator,
        ):
            pipeline = RaceStrategyPipeline()

            # Test individual formatting methods work together
            course_data = pipeline._format_course_data(integration_course)
            elevation_data = pipeline._format_elevation_data(integration_course)

            mock_metrics = mock_difficulty_calculator.calculate_difficulty.return_value
            difficulty_data = pipeline._format_difficulty_metrics(mock_metrics)
            crux_data = pipeline._format_crux_segments(mock_metrics.crux_segments)

            # All formatted data should be strings
            assert isinstance(course_data, str)
            assert isinstance(elevation_data, str)
            assert isinstance(difficulty_data, str)
            assert isinstance(crux_data, str)

            # Should contain relevant course information
            assert integration_course.name in course_data
            assert "Mile" in elevation_data
            assert "Overall Difficulty Rating" in difficulty_data
            assert "Integration Climb" in crux_data

    def test_segment_analysis_with_multiple_climbs(
        self, integration_course, mock_difficulty_calculator
    ):
        """Test segment analysis handles multiple climbs correctly"""
        with patch(
            "src.pipelines.core_strategy.DifficultyCalculator",
            return_value=mock_difficulty_calculator,
        ):
            pipeline = RaceStrategyPipeline()

            mock_metrics = mock_difficulty_calculator.calculate_difficulty.return_value

            # Test formatting for each crux segment
            for segment in mock_metrics.crux_segments:
                segment_data = pipeline._format_segment_data(
                    segment, integration_course
                )
                segment_position = pipeline._format_segment_position(
                    segment, integration_course
                )

                assert segment["name"] in segment_data
                assert "Mile" in segment_position
                assert "Race Position" in segment_position


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
