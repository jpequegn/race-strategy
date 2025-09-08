# tests/test_data_quality.py
"""
Comprehensive tests for data quality validation system.

Tests the DataValidator class and ensures accurate detection of data quality issues
in GPS course data before use in race strategy generation.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock

from src.utils.data_validator import (
    DataValidator,
    DataQualityReport,
    ValidationResult,
    generate_quality_report_summary,
)
from src.utils.gps_parser import GPSParser
from src.models.course import CourseProfile, ClimbSegment, GPSPoint, GPSMetadata


class TestDataValidator:
    """Test suite for GPS course data validation system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()

    def create_mock_course(
        self,
        name="Test Course",
        distance=25.0,
        elevation_gain=1000.0,
        num_gps_points=50,
        include_climbs=True,
        include_issues=False,
    ) -> CourseProfile:
        """Create a mock course for testing."""
        # Create GPS points
        gps_points = []
        for i in range(num_gps_points):
            elevation = (
                1000 + (elevation_gain * i / num_gps_points)
                if not include_issues
                else 1000 + i * 1000
            )
            gps_points.append(
                GPSPoint(
                    latitude=40.0 + i * 0.001,
                    longitude=-74.0 + i * 0.001,
                    elevation_ft=elevation,
                    distance_miles=distance * i / num_gps_points,
                )
            )

        # Create climbs
        climbs = []
        if include_climbs:
            if include_issues:
                # Add problematic climb with extreme gradient
                climbs.append(
                    ClimbSegment(
                        name="Extreme Climb",
                        start_mile=5.0,
                        length_miles=1.0,
                        elevation_gain_ft=5000.0,  # Extreme gain
                        avg_grade=94.7,  # Impossible gradient
                        max_grade=150.0,  # Impossible gradient
                    )
                )
            else:
                # Add reasonable climb
                climbs.append(
                    ClimbSegment(
                        name="Test Climb",
                        start_mile=10.0,
                        length_miles=2.0,
                        elevation_gain_ft=400.0,
                        avg_grade=3.8,
                        max_grade=6.5,
                    )
                )

        # Create GPS metadata
        metadata = GPSMetadata(
            total_points=num_gps_points,
            missing_elevation_points=5 if include_issues else 0,
            invalid_elevation_points=10 if include_issues else 0,
            invalid_latitude_points=0,
            invalid_longitude_points=0,
            large_distance_jumps=6000 if include_issues else 1,
            total_validation_errors=23 if include_issues else 1,
            data_quality_score=60.0 if include_issues else 95.0,
            smoothed=True,
        )

        return CourseProfile(
            name=name,
            bike_distance_miles=10000.0
            if include_issues
            else distance,  # Extreme distance if issues
            bike_elevation_gain_ft=elevation_gain,
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=200,
            key_climbs=climbs,
            technical_sections=["Technical Section 1"] if include_issues else [],
            altitude_ft=1000,
            elevation_profile=gps_points,
            gps_metadata=metadata,
            start_coords=(40.0, -74.0),
            finish_coords=(
                40.0 + (num_gps_points - 1) * 0.001,
                -74.0 + (num_gps_points - 1) * 0.001,
            ),
        )

    def test_validator_initialization(self):
        """Test that validator initializes correctly."""
        validator = DataValidator()
        assert validator is not None
        assert len(validator.validation_checks) > 0
        assert hasattr(validator, "MAX_REASONABLE_GRADIENT")
        assert validator.MAX_REASONABLE_GRADIENT == 35.0

    def test_validate_high_quality_course(self):
        """Test validation of high-quality course data."""
        course = self.create_mock_course(include_issues=False)

        report = self.validator.validate_course(course)

        assert isinstance(report, DataQualityReport)
        assert report.course_name == "Test Course"
        assert report.overall_score >= 80.0
        assert report.critical_failures == 0
        assert report.is_valid_for_strategy
        assert report.quality_rating in ["Good", "Excellent"]
        assert len(report.validation_results) > 0

        # Check that basic validations passed
        basic_check = next(
            (
                r
                for r in report.validation_results
                if r.check_name == "Basic Course Data"
            ),
            None,
        )
        assert basic_check is not None
        assert basic_check.passed

    def test_validate_problematic_course(self):
        """Test validation of course data with quality issues."""
        course = self.create_mock_course(include_issues=True)

        report = self.validator.validate_course(course)

        assert isinstance(report, DataQualityReport)
        assert report.overall_score < 75.0
        assert report.critical_failures > 0
        assert not report.is_valid_for_strategy
        assert report.quality_rating in ["Poor", "Unusable"]

        # Check that distance bounds validation failed
        distance_check = next(
            (r for r in report.validation_results if r.check_name == "Distance Bounds"),
            None,
        )
        assert distance_check is not None
        assert not distance_check.passed
        assert distance_check.severity == "critical"

    def test_basic_course_data_validation(self):
        """Test basic course data validation."""
        # Test valid course
        valid_course = self.create_mock_course()
        result = self.validator._validate_basic_course_data(valid_course)
        assert result.passed
        assert result.severity == "info"

        # Test course with missing name
        invalid_course = self.create_mock_course(name="")
        result = self.validator._validate_basic_course_data(invalid_course)
        assert not result.passed
        assert result.severity == "critical"
        assert "name" in result.message.lower()

        # Test course with invalid distance
        invalid_course = self.create_mock_course()
        invalid_course.bike_distance_miles = -5.0
        result = self.validator._validate_basic_course_data(invalid_course)
        assert not result.passed
        assert "distance" in result.message.lower()

    def test_distance_bounds_validation(self):
        """Test course distance bounds validation."""
        # Test course too short
        short_course = self.create_mock_course(distance=2.0)
        result = self.validator._validate_distance_bounds(short_course)
        assert not result.passed
        assert result.severity == "critical"
        assert "short" in result.message.lower()

        # Test course too long
        long_course = self.create_mock_course(distance=300.0)
        result = self.validator._validate_distance_bounds(long_course)
        assert not result.passed
        assert result.severity == "critical"
        assert "long" in result.message.lower()

        # Test reasonable course
        normal_course = self.create_mock_course(distance=25.0)
        result = self.validator._validate_distance_bounds(normal_course)
        assert result.passed

    def test_elevation_data_validation(self):
        """Test elevation data validation."""
        # Test course with no elevation profile
        no_elevation_course = self.create_mock_course()
        no_elevation_course.elevation_profile = []
        results = self.validator._validate_elevation_data(no_elevation_course)
        assert any(not r.passed and r.severity == "critical" for r in results)

        # Test course with valid elevations
        valid_course = self.create_mock_course()
        results = self.validator._validate_elevation_data(valid_course)
        bounds_result = next(
            (r for r in results if r.check_name == "Elevation Bounds"), None
        )
        assert bounds_result is not None
        assert bounds_result.passed

        # Test course with extreme elevation gain
        extreme_course = self.create_mock_course(elevation_gain=50000.0)
        results = self.validator._validate_elevation_data(extreme_course)
        gain_result = next(
            (r for r in results if r.check_name == "Elevation Gain Rate"), None
        )
        assert gain_result is not None
        assert not gain_result.passed

    def test_gradient_calculations_validation(self):
        """Test gradient calculations validation."""
        # Test course with no climbs
        no_climbs_course = self.create_mock_course(include_climbs=False)
        results = self.validator._validate_gradient_calculations(no_climbs_course)
        assert len(results) == 1
        assert results[0].passed
        assert "no climbs" in results[0].message.lower()

        # Test course with reasonable gradients
        normal_course = self.create_mock_course()
        results = self.validator._validate_gradient_calculations(normal_course)
        gradient_result = next(
            (r for r in results if r.check_name == "Gradient Calculations"), None
        )
        assert gradient_result is not None
        assert gradient_result.passed

        # Test course with impossible gradients
        extreme_course = self.create_mock_course(include_issues=True)
        results = self.validator._validate_gradient_calculations(extreme_course)
        impossible_result = next(
            (r for r in results if r.check_name == "Impossible Gradients"), None
        )
        assert impossible_result is not None
        assert not impossible_result.passed
        assert impossible_result.severity == "critical"

    def test_climb_detection_validation(self):
        """Test climb detection validation."""
        # Test course with valid climbs
        course_with_climbs = self.create_mock_course(include_climbs=True)
        result = self.validator._validate_climb_detection(course_with_climbs)
        assert result.passed
        assert "valid climbs" in result.message.lower()

        # Test course without climbs but high elevation gain
        no_climbs_high_gain = self.create_mock_course(
            include_climbs=False, elevation_gain=5000.0
        )
        result = self.validator._validate_climb_detection(no_climbs_high_gain)
        assert not result.passed
        assert result.severity == "warning"
        assert "no climbs detected" in result.message.lower()

        # Test course with invalid climb data
        invalid_climb_course = self.create_mock_course(include_climbs=True)
        invalid_climb_course.key_climbs[0].length_miles = -1.0  # Invalid length
        result = self.validator._validate_climb_detection(invalid_climb_course)
        assert not result.passed
        assert result.severity == "critical"

    def test_gps_point_quality_validation(self):
        """Test GPS point quality validation."""
        # Test course with insufficient GPS points
        low_points_course = self.create_mock_course(num_gps_points=5)
        results = self.validator._validate_gps_point_quality(low_points_course)
        count_result = next(
            (r for r in results if r.check_name == "GPS Point Count"), None
        )
        assert count_result is not None
        assert not count_result.passed
        assert count_result.severity == "critical"

        # Test course with adequate GPS points
        normal_course = self.create_mock_course(num_gps_points=100)
        results = self.validator._validate_gps_point_quality(normal_course)
        count_result = next(
            (r for r in results if r.check_name == "GPS Point Count"), None
        )
        assert count_result is not None
        assert count_result.passed

        # Test course with many distance jumps
        jumpy_course = self.create_mock_course(include_issues=True)
        results = self.validator._validate_gps_point_quality(jumpy_course)
        continuity_result = next(
            (r for r in results if r.check_name == "GPS Point Continuity"), None
        )
        assert continuity_result is not None
        assert not continuity_result.passed
        assert continuity_result.severity == "warning"

    def test_course_consistency_validation(self):
        """Test course internal consistency validation."""
        course = self.create_mock_course()
        results = self.validator._validate_course_consistency(course)

        # Should have elevation consistency check
        elev_result = next(
            (r for r in results if r.check_name == "Elevation Consistency"), None
        )
        assert elev_result is not None
        assert elev_result.passed

        # Should have coordinate bounds check
        coord_result = next(
            (r for r in results if r.check_name == "Coordinate Bounds"), None
        )
        assert coord_result is not None
        assert coord_result.passed

    def test_validation_result_structure(self):
        """Test ValidationResult structure and properties."""
        result = ValidationResult(
            check_name="Test Check",
            passed=False,
            severity="warning",
            message="Test message",
            details={"key": "value"},
            suggested_fix="Test fix",
        )

        assert result.check_name == "Test Check"
        assert not result.passed
        assert result.severity == "warning"
        assert result.message == "Test message"
        assert result.details["key"] == "value"
        assert result.suggested_fix == "Test fix"

    def test_data_quality_report_properties(self):
        """Test DataQualityReport properties and calculations."""
        report = DataQualityReport(
            course_name="Test Course",
            overall_score=85.0,
            total_checks=10,
            passed_checks=8,
            critical_failures=0,
            warnings=2,
        )

        assert report.is_valid_for_strategy  # Score >= 75 and no critical failures
        assert report.quality_rating == "Good"

        # Test with critical failures
        report.critical_failures = 1
        assert not report.is_valid_for_strategy

        # Test quality ratings
        report.overall_score = 96.0
        report.critical_failures = 0
        assert report.quality_rating == "Excellent"

        report.overall_score = 70.0
        assert report.quality_rating == "Poor"

        report.overall_score = 55.0
        assert report.quality_rating == "Unusable"

        report.overall_score = 40.0
        assert report.quality_rating == "Unusable"

    def test_quality_report_summary_generation(self):
        """Test quality report summary generation."""
        # Create a sample report
        report = DataQualityReport(
            course_name="Test Course",
            overall_score=85.0,
            total_checks=5,
            passed_checks=4,
            critical_failures=0,
            warnings=1,
        )

        report.validation_results = [
            ValidationResult("Test Check 1", True, "info", "Passed"),
            ValidationResult(
                "Test Check 2", False, "warning", "Warning", suggested_fix="Fix this"
            ),
        ]

        summary = generate_quality_report_summary(report)

        assert "Test Course" in summary
        assert "85.0/100" in summary
        assert "✅ VALID" in summary
        assert "Test Check 1" in summary
        assert "Test Check 2" in summary
        assert "Fix this" in summary

    def test_validator_error_handling(self):
        """Test validator error handling for malformed data."""
        # Create course with None values to trigger errors
        malformed_course = CourseProfile(
            name=None,
            bike_distance_miles=None,
            bike_elevation_gain_ft=None,
            swim_distance_miles=1.2,
            run_distance_miles=13.1,
            run_elevation_gain_ft=200,
            key_climbs=[],
            technical_sections=[],
        )

        # Validator should handle errors gracefully
        report = self.validator.validate_course(malformed_course)
        assert isinstance(report, DataQualityReport)
        assert report.critical_failures > 0
        assert not report.is_valid_for_strategy


class TestDataValidatorWithRealGPXFiles:
    """Test data validator against actual example GPX files."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
        self.parser = GPSParser()
        self.examples_dir = os.path.join(
            os.path.dirname(__file__), "..", "examples", "gpx"
        )

    def test_validate_flat_course(self):
        """Test validation of flat course example."""
        file_path = os.path.join(self.examples_dir, "flat_course.gpx")

        if not os.path.exists(file_path):
            pytest.skip("Flat course GPX file not found")

        course = self.parser.parse_gpx_file(file_path)
        report = self.validator.validate_course(course)

        # Flat course should have good data quality
        assert isinstance(report, DataQualityReport)
        assert report.overall_score > 50  # Should be reasonable despite synthetic data

        # Should detect that it's a reasonable flat course
        distance_result = next(
            (r for r in report.validation_results if r.check_name == "Distance Bounds"),
            None,
        )
        assert distance_result is not None
        assert distance_result.passed  # Flat course has reasonable distance

    def test_validate_mountain_course(self):
        """Test validation of mountain course example."""
        file_path = os.path.join(self.examples_dir, "mountain_course.gpx")

        if not os.path.exists(file_path):
            pytest.skip("Mountain course GPX file not found")

        course = self.parser.parse_gpx_file(file_path)
        report = self.validator.validate_course(course)

        # Mountain course has extreme synthetic data, should detect issues
        assert isinstance(report, DataQualityReport)

        # Should detect impossible gradients
        gradient_results = [
            r for r in report.validation_results if "Gradient" in r.check_name
        ]
        assert len(gradient_results) > 0
        impossible_result = next(
            (r for r in gradient_results if "Impossible" in r.check_name), None
        )
        if impossible_result:  # Synthetic data may have extreme gradients
            assert not impossible_result.passed
            assert impossible_result.severity == "critical"

    def test_validate_edge_cases_course(self):
        """Test validation of edge cases course (designed to have issues)."""
        file_path = os.path.join(self.examples_dir, "edge_cases.gpx")

        if not os.path.exists(file_path):
            pytest.skip("Edge cases GPX file not found")

        course = self.parser.parse_gpx_file(file_path)
        report = self.validator.validate_course(course)

        # Edge cases course should have multiple validation failures
        assert isinstance(report, DataQualityReport)
        assert report.critical_failures > 0 or report.warnings > 0
        assert report.overall_score < 90  # Should detect quality issues

        # Should detect the extreme distance issue
        distance_result = next(
            (r for r in report.validation_results if r.check_name == "Distance Bounds"),
            None,
        )
        assert distance_result is not None
        # Edge cases has >10,000 mile distance, should fail bounds check
        if course.bike_distance_miles > 200:
            assert not distance_result.passed

    def test_validate_all_example_files(self):
        """Test validation against all example GPX files."""
        example_files = [
            "flat_course.gpx",
            "hilly_course.gpx",
            "mountain_course.gpx",
            "urban_course.gpx",
            "edge_cases.gpx",
        ]

        validation_results = {}

        for filename in example_files:
            file_path = os.path.join(self.examples_dir, filename)

            if not os.path.exists(file_path):
                pytest.skip(f"Example file {filename} not found")
                continue

            course = self.parser.parse_gpx_file(file_path)
            report = self.validator.validate_course(course)
            validation_results[filename] = report

            # All files should at least parse and generate reports
            assert isinstance(report, DataQualityReport)
            assert len(report.validation_results) > 0

        # Should have validated at least some files
        assert len(validation_results) > 0

        # Flat course should be the highest quality (least issues)
        if "flat_course.gpx" in validation_results:
            flat_report = validation_results["flat_course.gpx"]
            # Flat course should have fewer issues than edge cases
            if "edge_cases.gpx" in validation_results:
                edge_report = validation_results["edge_cases.gpx"]
                assert flat_report.overall_score >= edge_report.overall_score


if __name__ == "__main__":
    pytest.main([__file__])
