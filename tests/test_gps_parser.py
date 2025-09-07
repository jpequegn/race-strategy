# tests/test_gps_parser.py
import pytest
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock

from src.utils.gps_parser import GPSParser, GPSParserConfig
from src.models.course import CourseProfile, GPSPoint


class TestGPSParser:
    """Test suite for GPS parser functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = GPSParser()
        self.sample_gpx_content = """<?xml version="1.0"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Test Course</name>
    <trkseg>
      <trkpt lat="40.0000" lon="-74.0000">
        <ele>100</ele>
      </trkpt>
      <trkpt lat="40.0010" lon="-74.0000">
        <ele>150</ele>
      </trkpt>
      <trkpt lat="40.0020" lon="-74.0000">
        <ele>200</ele>
      </trkpt>
      <trkpt lat="40.0030" lon="-74.0000">
        <ele>250</ele>
      </trkpt>
      <trkpt lat="40.0040" lon="-74.0000">
        <ele>300</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""

    def create_temp_gpx(self, content: str) -> str:
        """Create temporary GPX file for testing"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
            f.write(content)
            return f.name

    def test_parser_initialization(self):
        """Test GPS parser initialization with custom parameters"""
        parser = GPSParser(min_climb_grade=4.0, min_climb_distance=0.3)
        assert parser.min_climb_grade == 4.0
        assert parser.min_climb_distance == 0.3

    def test_parse_gpx_file_success(self):
        """Test successful GPX file parsing"""
        gpx_file = self.create_temp_gpx(self.sample_gpx_content)

        try:
            course = self.parser.parse_gpx_file(gpx_file)

            # Basic validation
            assert isinstance(course, CourseProfile)
            assert course.name == "Test Course"
            assert course.bike_distance_miles > 0
            assert course.bike_elevation_gain_ft > 0
            assert course.gps_metadata is not None
            assert len(course.elevation_profile) == 5
            assert course.start_coords is not None
            assert course.finish_coords is not None

        finally:
            os.unlink(gpx_file)

    def test_parse_gpx_file_not_found(self):
        """Test handling of missing GPX file"""
        with pytest.raises(FileNotFoundError):
            self.parser.parse_gpx_file("nonexistent.gpx")

    def test_parse_invalid_gpx(self):
        """Test handling of invalid GPX content"""
        invalid_gpx = "<?xml version='1.0'?><invalid>content</invalid>"
        gpx_file = self.create_temp_gpx(invalid_gpx)

        try:
            with pytest.raises(
                ValueError
            ):  # Could be "No tracks found" or "Invalid GPX file format"
                self.parser.parse_gpx_file(gpx_file)
        finally:
            os.unlink(gpx_file)

    def test_parse_empty_gpx(self):
        """Test handling of GPX with no tracks"""
        empty_gpx = """<?xml version="1.0"?>
<gpx version="1.1" creator="Test">
</gpx>"""
        gpx_file = self.create_temp_gpx(empty_gpx)

        try:
            with pytest.raises(ValueError, match="No tracks found"):
                self.parser.parse_gpx_file(gpx_file)
        finally:
            os.unlink(gpx_file)

    def test_gradient_calculation(self):
        """Test gradient calculation between GPS points"""
        # Create GPS points with known elevation changes
        gps_points = [
            GPSPoint(40.0000, -74.0000, 100.0, 0.0),
            GPSPoint(40.0010, -74.0000, 150.0, 0.069),  # ~0.069 miles between points
            GPSPoint(40.0020, -74.0000, 200.0, 0.138),
            GPSPoint(40.0030, -74.0000, 150.0, 0.207),  # Descent
        ]

        self.parser._calculate_gradients(gps_points)

        # Check that gradients were calculated (allowing for some precision variance)
        assert gps_points[1].gradient_percent > 0  # Uphill
        assert gps_points[2].gradient_percent > 0  # Uphill
        assert gps_points[3].gradient_percent < 0  # Downhill

    def test_climb_detection(self):
        """Test climb detection algorithm"""
        # Create GPS points with a defined climb (long enough to meet minimum distance)
        gps_points = [
            GPSPoint(40.0000, -74.0000, 100.0, 0.0, 0.0),
            GPSPoint(40.0010, -74.0000, 120.0, 0.2, 4.0),  # Start climb
            GPSPoint(40.0020, -74.0000, 140.0, 0.4, 4.0),  # Continue climb
            GPSPoint(40.0030, -74.0000, 160.0, 0.6, 4.0),  # Continue climb
            GPSPoint(40.0040, -74.0000, 180.0, 0.8, 4.0),  # Continue climb
            GPSPoint(
                40.0050, -74.0000, 185.0, 1.0, -1.0
            ),  # End climb with descent (total 0.8 miles)
        ]

        climbs = self.parser._detect_climbs(gps_points)

        assert len(climbs) == 1
        climb = climbs[0]
        assert climb.avg_grade >= self.parser.min_climb_grade
        assert climb.length_miles >= self.parser.min_climb_distance
        assert climb.start_coords is not None
        assert climb.end_coords is not None

    def test_short_climb_filtering(self):
        """Test that climbs shorter than minimum distance are filtered out"""
        # Create a short, steep climb
        gps_points = [
            GPSPoint(40.0000, -74.0000, 100.0, 0.0, 0.0),
            GPSPoint(40.0010, -74.0000, 120.0, 0.1, 8.0),  # Short but steep
            GPSPoint(40.0020, -74.0000, 125.0, 0.2, 1.0),  # End climb
        ]

        climbs = self.parser._detect_climbs(gps_points)

        # Should be filtered out because it's too short
        assert len(climbs) == 0

    def test_elevation_gain_calculation(self):
        """Test total elevation gain calculation"""
        gps_points = [
            GPSPoint(40.0000, -74.0000, 100.0, 0.0),
            GPSPoint(40.0010, -74.0000, 150.0, 0.1),  # +50ft
            GPSPoint(40.0020, -74.0000, 120.0, 0.2),  # -30ft (ignored)
            GPSPoint(40.0030, -74.0000, 180.0, 0.3),  # +60ft
        ]

        total_gain = self.parser._calculate_total_elevation_gain(gps_points)

        # Should be 50 + 60 = 110ft (descents ignored)
        assert total_gain == 110.0

    def test_technical_sections_detection(self):
        """Test detection of technical sections like steep descents"""
        gps_points = [
            GPSPoint(40.0000, -74.0000, 300.0, 0.0, 0.0),
            GPSPoint(40.0010, -74.0000, 250.0, 0.3, -10.0),  # Steep descent
            GPSPoint(40.0020, -74.0000, 200.0, 0.6, -10.0),  # Continue descent
            GPSPoint(40.0030, -74.0000, 190.0, 0.8, -2.0),  # End descent
        ]

        technical_sections = self.parser._identify_technical_sections(gps_points)

        assert len(technical_sections) > 0
        assert "Steep descent" in technical_sections[0]

    def test_metadata_generation(self):
        """Test GPS metadata generation"""
        # Mock track points with some missing elevation
        track_points = [
            Mock(elevation=100, latitude=40.0, longitude=-74.0),
            Mock(elevation=None, latitude=40.1, longitude=-74.1),  # Missing elevation
            Mock(elevation=200, latitude=40.2, longitude=-74.2),
        ]

        gps_points = [
            GPSPoint(40.0, -74.0, 100.0, 0.0),
            GPSPoint(40.1, -74.1, 0.0, 0.1),
            GPSPoint(40.2, -74.2, 200.0, 0.2),
        ]

        metadata = self.parser._generate_metadata("test.gpx", gps_points, track_points)

        assert metadata.source_file == "test.gpx"
        assert metadata.total_points == 3
        assert metadata.missing_elevation_points == 1
        assert metadata.data_quality_score < 100  # Penalized for missing data
        assert metadata.bounds is not None
        assert isinstance(metadata.parsed_at, datetime)

    def test_data_smoothing(self):
        """Test data smoothing functionality"""
        noisy_data = [100, 95, 105, 98, 108, 102, 112]
        smoothed = self.parser._smooth_data(noisy_data, window=3)

        assert len(smoothed) == len(noisy_data)
        # Smoothed data should be less extreme than original
        assert max(smoothed) <= max(noisy_data)
        assert min(smoothed) >= min(noisy_data)

    def test_empty_gps_points_handling(self):
        """Test handling of empty GPS points list"""
        empty_points = []

        # Should not crash
        self.parser._calculate_gradients(empty_points)
        climbs = self.parser._detect_climbs(empty_points)
        technical = self.parser._identify_technical_sections(empty_points)
        elevation_gain = self.parser._calculate_total_elevation_gain(empty_points)

        assert climbs == []
        assert technical == []
        assert elevation_gain == 0.0

    def test_gps_parser_config_default_values(self):
        """Test GPSParserConfig has correct default values"""
        config = GPSParserConfig()
        assert config.min_climb_grade == 3.0
        assert config.min_climb_distance == 0.5
        assert config.descent_threshold == -8.0
        assert config.min_descent_length == 0.2
        assert config.smoothing_window == 5
        assert config.quality_penalty_factor == 50.0
        assert config.descent_continuation_threshold == -3.0

    def test_gps_parser_config_custom_values(self):
        """Test GPSParserConfig with custom values"""
        config = GPSParserConfig(
            min_climb_grade=4.0,
            min_climb_distance=0.3,
            descent_threshold=-10.0,
            min_descent_length=0.15,
            smoothing_window=3,
            quality_penalty_factor=75.0,
        )
        assert config.min_climb_grade == 4.0
        assert config.min_climb_distance == 0.3
        assert config.descent_threshold == -10.0
        assert config.min_descent_length == 0.15
        assert config.smoothing_window == 3
        assert config.quality_penalty_factor == 75.0

    def test_parser_with_config_object(self):
        """Test GPS parser initialization with config object"""
        config = GPSParserConfig(
            min_climb_grade=5.0, min_climb_distance=0.8, smoothing_window=7
        )
        parser = GPSParser(config=config)

        assert parser.config.min_climb_grade == 5.0
        assert parser.config.min_climb_distance == 0.8
        assert parser.config.smoothing_window == 7
        # Backward compatibility attributes
        assert parser.min_climb_grade == 5.0
        assert parser.min_climb_distance == 0.8

    def test_parser_backward_compatibility(self):
        """Test GPS parser backward compatibility with old parameters"""
        parser = GPSParser(min_climb_grade=4.5, min_climb_distance=0.7)

        assert parser.config.min_climb_grade == 4.5
        assert parser.config.min_climb_distance == 0.7
        # Should still use default values for other parameters
        assert parser.config.smoothing_window == 5
        assert parser.config.descent_threshold == -8.0

    def test_parser_default_config(self):
        """Test GPS parser uses default config when no parameters provided"""
        parser = GPSParser()

        assert parser.config.min_climb_grade == 3.0
        assert parser.config.min_climb_distance == 0.5
        assert parser.config.smoothing_window == 5
        assert parser.config.descent_threshold == -8.0
        assert parser.config.min_descent_length == 0.2
        assert parser.config.quality_penalty_factor == 50.0

    def test_custom_smoothing_window_in_gradient_calculation(self):
        """Test that custom smoothing window is used in gradient calculation"""
        config = GPSParserConfig(smoothing_window=3)
        parser = GPSParser(config=config)

        gps_points = [
            GPSPoint(40.0000, -74.0000, 100.0, 0.0),
            GPSPoint(40.0010, -74.0000, 110.0, 0.069),
            GPSPoint(40.0020, -74.0000, 120.0, 0.138),
        ]

        # This should work without error using custom smoothing window
        parser._calculate_gradients(gps_points)
        assert gps_points[1].gradient_percent is not None
        assert gps_points[2].gradient_percent is not None

    def test_custom_quality_penalty_factor(self):
        """Test custom quality penalty factor in metadata generation"""
        config = GPSParserConfig(
            quality_penalty_factor=25.0
        )  # Half the default penalty
        parser = GPSParser(config=config)

        # Mock track points with 50% missing elevation
        track_points = [
            Mock(elevation=100, latitude=40.0, longitude=-74.0),
            Mock(elevation=None, latitude=40.1, longitude=-74.1),  # Missing elevation
        ]

        gps_points = [
            GPSPoint(40.0, -74.0, 100.0, 0.0),
            GPSPoint(40.1, -74.1, 0.0, 0.1),
        ]

        metadata = parser._generate_metadata("test.gpx", gps_points, track_points)

        # With 50% missing elevation and penalty factor 25.0:
        # quality_score = 100 - (0.5 * 25.0) = 87.5
        assert metadata.data_quality_score == 87.5

    def test_custom_descent_detection_parameters(self):
        """Test custom descent threshold and minimum length"""
        config = GPSParserConfig(
            descent_threshold=-5.0,  # Less steep threshold
            min_descent_length=0.1,  # Shorter minimum length
            descent_continuation_threshold=-2.0,  # Allow gentler continuation
        )
        parser = GPSParser(config=config)

        # Create GPS points with a moderate descent that would be detected with custom params
        gps_points = [
            GPSPoint(40.0000, -74.0000, 300.0, 0.0, 0.0),
            GPSPoint(40.0010, -74.0000, 285.0, 0.15, -6.0),  # Moderate descent
            GPSPoint(40.0020, -74.0000, 280.0, 0.25, -2.5),  # Continue descent
        ]

        technical_sections = parser._identify_technical_sections(gps_points)

        # Should detect the descent with custom parameters
        assert len(technical_sections) > 0
        assert "Steep descent" in technical_sections[0]

    def test_coordinate_validation_config_defaults(self):
        """Test coordinate validation config has correct default values"""
        config = GPSParserConfig()

        # Coordinate bounds
        assert config.min_latitude == -90.0
        assert config.max_latitude == 90.0
        assert config.min_longitude == -180.0
        assert config.max_longitude == 180.0

        # Elevation bounds
        assert config.min_elevation_ft == -1000.0
        assert config.max_elevation_ft == 30000.0

        # Distance validation
        assert config.max_distance_jump_miles == 1.0
        assert config.coordinate_validation_penalty == 20.0

    def test_invalid_latitude_coordinates(self):
        """Test detection of invalid latitude coordinates"""
        invalid_gpx = """<?xml version="1.0"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Invalid Latitude Test</name>
    <trkseg>
      <trkpt lat="95.0000" lon="-74.0000">
        <ele>100</ele>
      </trkpt>
      <trkpt lat="40.0000" lon="-74.0000">
        <ele>150</ele>
      </trkpt>
      <trkpt lat="-95.0000" lon="-74.0000">
        <ele>200</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""
        gpx_file = self.create_temp_gpx(invalid_gpx)

        try:
            course = self.parser.parse_gpx_file(gpx_file)

            # Check validation results in metadata
            assert course.gps_metadata.invalid_latitude_points == 2
            assert course.gps_metadata.total_validation_errors >= 2
            assert course.gps_metadata.data_quality_score < 100

        finally:
            os.unlink(gpx_file)

    def test_invalid_longitude_coordinates(self):
        """Test detection of invalid longitude coordinates"""
        invalid_gpx = """<?xml version="1.0"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Invalid Longitude Test</name>
    <trkseg>
      <trkpt lat="40.0000" lon="-190.0000">
        <ele>100</ele>
      </trkpt>
      <trkpt lat="40.0010" lon="-74.0000">
        <ele>150</ele>
      </trkpt>
      <trkpt lat="40.0020" lon="185.0000">
        <ele>200</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""
        gpx_file = self.create_temp_gpx(invalid_gpx)

        try:
            course = self.parser.parse_gpx_file(gpx_file)

            # Check validation results in metadata
            assert course.gps_metadata.invalid_longitude_points == 2
            assert course.gps_metadata.total_validation_errors >= 2
            assert course.gps_metadata.data_quality_score < 100

        finally:
            os.unlink(gpx_file)

    def test_invalid_elevation_values(self):
        """Test detection of invalid elevation values"""
        invalid_gpx = """<?xml version="1.0"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Invalid Elevation Test</name>
    <trkseg>
      <trkpt lat="40.0000" lon="-74.0000">
        <ele>-500</ele>
      </trkpt>
      <trkpt lat="40.0010" lon="-74.0000">
        <ele>10000</ele>
      </trkpt>
      <trkpt lat="40.0020" lon="-74.0000">
        <ele>200</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""
        gpx_file = self.create_temp_gpx(invalid_gpx)

        try:
            course = self.parser.parse_gpx_file(gpx_file)

            # Check validation results in metadata
            assert course.gps_metadata.invalid_elevation_points == 2
            assert course.gps_metadata.total_validation_errors >= 2
            assert course.gps_metadata.data_quality_score < 100

        finally:
            os.unlink(gpx_file)

    def test_gps_loss_detection(self):
        """Test detection of GPS loss (0, 0) coordinates"""
        gps_loss_gpx = """<?xml version="1.0"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>GPS Loss Test</name>
    <trkseg>
      <trkpt lat="40.0000" lon="-74.0000">
        <ele>100</ele>
      </trkpt>
      <trkpt lat="0.0000" lon="0.0000">
        <ele>150</ele>
      </trkpt>
      <trkpt lat="40.0020" lon="-74.0000">
        <ele>200</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""
        gpx_file = self.create_temp_gpx(gps_loss_gpx)

        try:
            course = self.parser.parse_gpx_file(gpx_file)

            # GPS loss should be detected as both invalid latitude and longitude
            assert course.gps_metadata.invalid_latitude_points >= 1
            assert course.gps_metadata.invalid_longitude_points >= 1
            assert course.gps_metadata.total_validation_errors >= 2
            assert course.gps_metadata.data_quality_score < 100

        finally:
            os.unlink(gpx_file)

    def test_large_distance_jumps(self):
        """Test detection of unrealistic distance jumps between points"""
        # Create GPS data with a large distance jump (> 1 mile default threshold)
        distance_jump_gpx = """<?xml version="1.0"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Distance Jump Test</name>
    <trkseg>
      <trkpt lat="40.0000" lon="-74.0000">
        <ele>100</ele>
      </trkpt>
      <trkpt lat="40.0010" lon="-74.0000">
        <ele>150</ele>
      </trkpt>
      <trkpt lat="41.0000" lon="-74.0000">
        <ele>200</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""
        gpx_file = self.create_temp_gpx(distance_jump_gpx)

        try:
            course = self.parser.parse_gpx_file(gpx_file)

            # Check for large distance jump detection
            assert course.gps_metadata.large_distance_jumps >= 1
            assert course.gps_metadata.total_validation_errors >= 1
            assert course.gps_metadata.data_quality_score < 100

        finally:
            os.unlink(gpx_file)

    def test_coordinate_validation_data_quality_scoring(self):
        """Test data quality score calculation with validation errors"""
        config = GPSParserConfig(coordinate_validation_penalty=30.0)
        parser = GPSParser(config=config)

        # Create GPS data with multiple validation errors
        multi_error_gpx = """<?xml version="1.0"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Multiple Errors Test</name>
    <trkseg>
      <trkpt lat="40.0000" lon="-74.0000">
        <ele>100</ele>
      </trkpt>
      <trkpt lat="95.0000" lon="185.0000">
        <ele>50000</ele>
      </trkpt>
      <trkpt lat="40.0020" lon="-74.0000">
        <ele>200</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""
        gpx_file = self.create_temp_gpx(multi_error_gpx)

        try:
            course = parser.parse_gpx_file(gpx_file)

            # Should have multiple validation errors affecting quality score
            assert course.gps_metadata.total_validation_errors >= 3

            # With 3 errors out of 3 points and penalty 30.0:
            # quality reduction = (3/3) * 30.0 = 30.0
            # So quality score should be around 70.0 or less
            assert course.gps_metadata.data_quality_score <= 70.0

        finally:
            os.unlink(gpx_file)

    def test_custom_validation_thresholds(self):
        """Test coordinate validation with custom thresholds"""
        config = GPSParserConfig(
            min_latitude=-45.0,
            max_latitude=45.0,
            min_longitude=-90.0,
            max_longitude=90.0,
            min_elevation_ft=0.0,
            max_elevation_ft=10000.0,
            max_distance_jump_miles=0.5,
        )
        parser = GPSParser(config=config)

        # Create GPS data that would be valid with default thresholds but invalid with custom ones
        custom_threshold_gpx = """<?xml version="1.0"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Custom Thresholds Test</name>
    <trkseg>
      <trkpt lat="60.0000" lon="-100.0000">
        <ele>15000</ele>
      </trkpt>
      <trkpt lat="40.0000" lon="-74.0000">
        <ele>5000</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""
        gpx_file = self.create_temp_gpx(custom_threshold_gpx)

        try:
            course = parser.parse_gpx_file(gpx_file)

            # Should detect validation errors with custom thresholds
            assert course.gps_metadata.invalid_latitude_points >= 1  # lat 60 > 45
            assert course.gps_metadata.invalid_longitude_points >= 1  # lon -100 < -90
            assert (
                course.gps_metadata.invalid_elevation_points >= 1
            )  # ele 15000 > 10000
            assert course.gps_metadata.total_validation_errors >= 3

        finally:
            os.unlink(gpx_file)

    def test_validation_results_in_metadata(self):
        """Test that validation results are properly included in GPS metadata"""
        course = self.parser.parse_gpx_file(
            self.create_temp_gpx(self.sample_gpx_content)
        )

        # Valid GPS data should have no validation errors
        assert hasattr(course.gps_metadata, "invalid_latitude_points")
        assert hasattr(course.gps_metadata, "invalid_longitude_points")
        assert hasattr(course.gps_metadata, "invalid_elevation_points")
        assert hasattr(course.gps_metadata, "large_distance_jumps")
        assert hasattr(course.gps_metadata, "total_validation_errors")

        # All should be 0 for valid data
        assert course.gps_metadata.invalid_latitude_points == 0
        assert course.gps_metadata.invalid_longitude_points == 0
        assert course.gps_metadata.invalid_elevation_points == 0
        assert course.gps_metadata.large_distance_jumps == 0
        assert course.gps_metadata.total_validation_errors == 0

        # Quality score should be 100 for valid data
        assert course.gps_metadata.data_quality_score == 100.0

    def test_coordinate_bounds_validation(self):
        """Test individual coordinate bounds validation method"""
        # Test the _is_coordinate_valid helper method
        assert self.parser._is_coordinate_valid(45.0, -90.0, 90.0) is True
        assert self.parser._is_coordinate_valid(-45.0, -90.0, 90.0) is True
        assert self.parser._is_coordinate_valid(95.0, -90.0, 90.0) is False
        assert self.parser._is_coordinate_valid(-95.0, -90.0, 90.0) is False

        # Test edge cases
        assert (
            self.parser._is_coordinate_valid(90.0, -90.0, 90.0) is True
        )  # Exactly at boundary
        assert (
            self.parser._is_coordinate_valid(-90.0, -90.0, 90.0) is True
        )  # Exactly at boundary

    @pytest.fixture(autouse=True)
    def cleanup_temp_files(self):
        """Clean up any temporary files after tests"""
        yield
        # Cleanup is handled in individual tests


if __name__ == "__main__":
    pytest.main([__file__])
