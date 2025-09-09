# tests/integration/test_gps_integration.py
import os
import tempfile
from unittest.mock import patch

import pytest

from src.models.athlete import AthleteProfile
from src.models.conditions import RaceConditions
from src.models.course import CourseProfile
from src.pipelines.core_strategy import RaceStrategyPipeline
from src.utils.gps_parser import GPSParser


class TestGPSIntegration:
    """Integration tests for GPS parser with race strategy pipeline"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = GPSParser()

        # More realistic GPX content with climb
        self.realistic_gpx = """<?xml version="1.0"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Mountain Bike Course</name>
    <trkseg>
      <!-- Flat start -->
      <trkpt lat="40.0000" lon="-74.0000">
        <ele>100</ele>
      </trkpt>
      <trkpt lat="40.0100" lon="-74.0000">
        <ele>105</ele>
      </trkpt>
      <!-- Begin climb -->
      <trkpt lat="40.0200" lon="-74.0000">
        <ele>150</ele>
      </trkpt>
      <trkpt lat="40.0300" lon="-74.0000">
        <ele>200</ele>
      </trkpt>
      <trkpt lat="40.0400" lon="-74.0000">
        <ele>250</ele>
      </trkpt>
      <trkpt lat="40.0500" lon="-74.0000">
        <ele>300</ele>
      </trkpt>
      <trkpt lat="40.0600" lon="-74.0000">
        <ele>350</ele>
      </trkpt>
      <!-- Flat section -->
      <trkpt lat="40.0700" lon="-74.0000">
        <ele>355</ele>
      </trkpt>
      <trkpt lat="40.0800" lon="-74.0000">
        <ele>360</ele>
      </trkpt>
      <!-- Descent -->
      <trkpt lat="40.0900" lon="-74.0000">
        <ele>300</ele>
      </trkpt>
      <trkpt lat="40.1000" lon="-74.0000">
        <ele>250</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""

    def create_temp_gpx(self, content: str) -> str:
        """Create temporary GPX file for testing"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
            f.write(content)
            return f.name

    def test_full_gps_to_strategy_pipeline(self):
        """Test complete integration from GPX parsing to strategy generation"""
        gpx_file = self.create_temp_gpx(self.realistic_gpx)

        try:
            # Parse GPX to CourseProfile
            course = self.parser.parse_gpx_file(gpx_file)

            # Verify course was parsed correctly
            assert isinstance(course, CourseProfile)
            assert course.bike_distance_miles > 0
            assert len(course.key_climbs) > 0
            assert course.gps_metadata is not None
            assert course.gps_metadata.data_quality_score > 0

            # Create test athlete and conditions
            athlete = AthleteProfile(
                name="Test Athlete",
                ftp_watts=250,
                swim_pace_per_100m=90,
                run_threshold_pace=7.5,
                experience_level="intermediate",
                previous_70_3_time="5:45:00",
                strengths=["bike"],
                limiters=["swim"],
                target_finish_time="5:30:00",
            )

            conditions = RaceConditions(
                temperature_f=75,
                wind_speed_mph=8,
                wind_direction="variable",
                precipitation="none",
                humidity_percent=65,
            )

            # Mock the DSPy pipeline to avoid requiring API keys for tests
            with patch.object(
                RaceStrategyPipeline, "generate_strategy"
            ) as mock_generate:
                mock_generate.return_value = {
                    "course_analysis": self.create_mock_analysis(),
                    "athlete_assessment": self.create_mock_assessment(),
                    "pacing_strategy": self.create_mock_pacing(),
                    "risk_assessment": self.create_mock_risks(),
                    "final_strategy": self.create_mock_strategy(),
                }

                # Test that the course can be used in the pipeline
                pipeline = RaceStrategyPipeline()
                result = pipeline.generate_strategy(course, athlete, conditions)

                # Verify pipeline was called with GPS-enhanced course
                mock_generate.assert_called_once_with(course, athlete, conditions)
                assert "final_strategy" in result

        finally:
            os.unlink(gpx_file)

    def test_course_profile_gps_metadata_accessibility(self):
        """Test that GPS metadata is properly accessible in CourseProfile"""
        gpx_file = self.create_temp_gpx(self.realistic_gpx)

        try:
            course = self.parser.parse_gpx_file(gpx_file)

            # Test GPS metadata access
            assert course.gps_metadata.source_file.endswith(".gpx")
            assert course.gps_metadata.total_points > 0
            assert course.gps_metadata.data_quality_score >= 0
            assert course.gps_metadata.bounds is not None

            # Test elevation profile access
            assert len(course.elevation_profile) > 0
            first_point = course.elevation_profile[0]
            assert first_point.latitude is not None
            assert first_point.longitude is not None
            assert first_point.elevation_ft >= 0

            # Test coordinates
            assert course.start_coords is not None
            assert course.finish_coords is not None
            assert len(course.start_coords) == 2
            assert len(course.finish_coords) == 2

        finally:
            os.unlink(gpx_file)

    def test_climb_segments_with_gps_data(self):
        """Test that climb segments include GPS-specific data"""
        gpx_file = self.create_temp_gpx(self.realistic_gpx)

        try:
            course = self.parser.parse_gpx_file(gpx_file)

            # Should have detected at least one climb
            assert len(course.key_climbs) > 0

            climb = course.key_climbs[0]

            # Check GPS-specific climb data
            assert climb.start_coords is not None
            assert climb.end_coords is not None
            assert len(climb.gps_points) > 0

            # Verify climb coordinates are realistic
            start_lat, start_lon = climb.start_coords
            end_lat, end_lon = climb.end_coords
            assert 39 < start_lat < 41  # Reasonable latitude range
            assert -75 < start_lon < -73  # Reasonable longitude range
            assert 39 < end_lat < 41
            assert -75 < end_lon < -73

        finally:
            os.unlink(gpx_file)

    def test_course_formatting_for_dspy(self):
        """Test that GPS-enhanced courses format properly for DSPy pipeline"""
        gpx_file = self.create_temp_gpx(self.realistic_gpx)

        try:
            course = self.parser.parse_gpx_file(gpx_file)

            # Mock the pipeline to test formatting
            with patch("src.pipelines.core_strategy.RaceStrategyPipeline"):
                pipeline = RaceStrategyPipeline()

                # Test that course data formats without errors
                formatted_data = pipeline._format_course_data(course)

                # Should contain GPS-specific information
                assert course.name in formatted_data
                assert str(course.bike_distance_miles) in formatted_data
                assert str(course.bike_elevation_gain_ft) in formatted_data

                # Should handle climbs with GPS data
                if course.key_climbs:
                    for climb in course.key_climbs:
                        assert (
                            climb.name in formatted_data
                            or str(climb.start_mile) in formatted_data
                        )

        finally:
            os.unlink(gpx_file)

    def create_mock_analysis(self):
        """Create mock course analysis result"""

        class MockAnalysis:
            analysis = "Mock course analysis with GPS data"
            key_segments = "GPS-detected climbs and technical sections"
            difficulty_rating = "7/10 based on elevation profile"

        return MockAnalysis()

    def create_mock_assessment(self):
        """Create mock athlete assessment result"""

        class MockAssessment:
            strengths_vs_course = "Strong climber, good for GPS-detected elevation"
            risk_areas = "Technical descents identified in GPS data"
            power_targets = "Use GPS grade data for power zones"

        return MockAssessment()

    def create_mock_pacing(self):
        """Create mock pacing strategy result"""

        class MockPacing:
            swim_strategy = "Conservative swim start"
            bike_strategy = "GPS-based power targeting on climbs"
            run_strategy = "Even effort based on GPS elevation profile"

        return MockPacing()

    def create_mock_risks(self):
        """Create mock risk assessment result"""

        class MockRisks:
            primary_risks = "GPS-identified technical sections"
            mitigation_plan = "Conservative pacing on steep descents"
            contingency_options = "Alternative lines through technical sections"

        return MockRisks()

    def create_mock_strategy(self):
        """Create mock final strategy result"""

        class MockStrategy:
            final_strategy = "GPS-enhanced race strategy with precise pacing"
            time_prediction = "5:25:00 based on GPS course profile"
            success_probability = "85% with GPS data confidence"
            key_success_factors = (
                "Execute GPS-based climb strategy, handle technical descents"
            )

        return MockStrategy()

    @pytest.fixture(autouse=True)
    def cleanup_temp_files(self):
        """Clean up any temporary files after tests"""
        yield
        # Cleanup is handled in individual tests


if __name__ == "__main__":
    pytest.main([__file__])
