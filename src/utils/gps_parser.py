# src/utils/gps_parser.py
import gpxpy
from geopy.distance import geodesic
from typing import List, Optional
from datetime import datetime
import logging
from dataclasses import dataclass

from ..models.course import CourseProfile, ClimbSegment, GPSPoint, GPSMetadata

logger = logging.getLogger(__name__)


@dataclass
class GPSParserConfig:
    """Configuration class for GPS parser parameters"""

    min_climb_grade: float = 3.0
    min_climb_distance: float = 0.5
    descent_threshold: float = -8.0
    min_descent_length: float = 0.2
    smoothing_window: int = 5
    quality_penalty_factor: float = 50.0
    descent_continuation_threshold: float = -3.0
    
    # Coordinate validation parameters
    min_latitude: float = -90.0
    max_latitude: float = 90.0
    min_longitude: float = -180.0
    max_longitude: float = 180.0
    min_elevation_ft: float = -1000.0
    max_elevation_ft: float = 30000.0
    max_distance_jump_miles: float = 1.0  # Maximum reasonable distance between adjacent points
    coordinate_validation_penalty: float = 20.0  # Quality score penalty per validation error


class GPSParser:
    """GPS data parser for GPX files with climb detection and data validation"""

    def __init__(
        self,
        config: Optional[GPSParserConfig] = None,
        min_climb_grade: Optional[float] = None,
        min_climb_distance: Optional[float] = None,
    ):
        """
        Initialize GPS parser with configuration parameters

        Args:
            config: GPSParserConfig instance with all parameters (preferred method)
            min_climb_grade: Minimum grade percentage to consider a climb (deprecated, use config)
            min_climb_distance: Minimum distance in miles for a climb segment (deprecated, use config)
        """
        # Use provided config or create default config
        if config is not None:
            self.config = config
        else:
            # Backward compatibility: create config from individual parameters
            self.config = GPSParserConfig()
            if min_climb_grade is not None:
                self.config.min_climb_grade = min_climb_grade
            if min_climb_distance is not None:
                self.config.min_climb_distance = min_climb_distance

        # Keep these attributes for backward compatibility
        self.min_climb_grade = self.config.min_climb_grade
        self.min_climb_distance = self.config.min_climb_distance

    def parse_gpx_file(self, file_path: str) -> CourseProfile:
        """
        Parse GPX file and convert to CourseProfile

        Args:
            file_path: Path to GPX file

        Returns:
            CourseProfile with GPS data populated

        Raises:
            FileNotFoundError: If GPX file doesn't exist
            ValueError: If GPX file is invalid or empty
        """
        try:
            with open(file_path, "r", encoding="utf-8") as gpx_file:
                gpx = gpxpy.parse(gpx_file)
        except FileNotFoundError:
            raise FileNotFoundError(f"GPX file not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Invalid GPX file format: {e}")

        if not gpx.tracks:
            raise ValueError("No tracks found in GPX file")

        # Extract track points from all segments
        track_points = []
        for track in gpx.tracks:
            for segment in track.segments:
                track_points.extend(segment.points)

        if not track_points:
            raise ValueError("No track points found in GPX file")

        logger.info(f"Processing {len(track_points)} GPS points from {file_path}")

        # Convert to GPS points with distance and elevation calculations
        gps_points = self._process_track_points(track_points)

        # Generate metadata
        metadata = self._generate_metadata(file_path, gps_points, track_points)

        # Detect climbs
        climbs = self._detect_climbs(gps_points)

        # Create course profile
        course_name = (
            gpx.tracks[0].name or f"GPX Course from {file_path.split('/')[-1]}"
        )

        # Calculate total distance and elevation gain
        total_distance = gps_points[-1].distance_miles if gps_points else 0
        total_elevation_gain = self._calculate_total_elevation_gain(gps_points)

        return CourseProfile(
            name=course_name,
            bike_distance_miles=total_distance,
            bike_elevation_gain_ft=int(total_elevation_gain),
            swim_distance_miles=0.0,  # GPX typically doesn't include swim
            run_distance_miles=0.0,  # Assuming bike course, can be extended
            run_elevation_gain_ft=0,
            key_climbs=climbs,
            technical_sections=self._identify_technical_sections(gps_points),
            gps_metadata=metadata,
            elevation_profile=gps_points,
            start_coords=(
                (gps_points[0].latitude, gps_points[0].longitude)
                if gps_points
                else None
            ),
            finish_coords=(
                (gps_points[-1].latitude, gps_points[-1].longitude)
                if gps_points
                else None
            ),
        )

    def _process_track_points(self, track_points: List) -> List[GPSPoint]:
        """Convert GPX track points to GPSPoints with distance and gradient"""
        gps_points = []
        total_distance = 0.0

        for i, point in enumerate(track_points):
            # Handle missing elevation data
            elevation_ft = 0.0
            if point.elevation is not None:
                elevation_ft = point.elevation * 3.28084  # Convert meters to feet

            # Calculate distance from previous point
            if i > 0:
                prev_point = track_points[i - 1]
                distance = geodesic(
                    (prev_point.latitude, prev_point.longitude),
                    (point.latitude, point.longitude),
                ).miles
                total_distance += distance

            gps_point = GPSPoint(
                latitude=point.latitude,
                longitude=point.longitude,
                elevation_ft=elevation_ft,
                distance_miles=total_distance,
            )

            gps_points.append(gps_point)

        # Calculate gradients using smoothed elevation profile
        self._calculate_gradients(gps_points)

        return gps_points

    def _calculate_gradients(
        self, gps_points: List[GPSPoint], smoothing_window: Optional[int] = None
    ) -> None:
        """Calculate gradients between GPS points with optional smoothing"""
        if len(gps_points) < 2:
            return

        # Use config smoothing window if not provided
        if smoothing_window is None:
            smoothing_window = self.config.smoothing_window

        # Smooth elevation data to reduce noise
        elevations = [p.elevation_ft for p in gps_points]
        if smoothing_window > 1:
            elevations = self._smooth_data(elevations, smoothing_window)

        # Calculate gradients
        for i in range(1, len(gps_points)):
            distance_diff = (
                gps_points[i].distance_miles - gps_points[i - 1].distance_miles
            )
            elevation_diff = elevations[i] - elevations[i - 1]

            if distance_diff > 0:
                # Convert to percentage grade
                gradient = (elevation_diff / (distance_diff * 5280)) * 100
                gps_points[i].gradient_percent = gradient

    def _smooth_data(self, data: List[float], window: int) -> List[float]:
        """Apply moving average smoothing to data"""
        if len(data) < window:
            return data

        smoothed = []
        for i in range(len(data)):
            start_idx = max(0, i - window // 2)
            end_idx = min(len(data), i + window // 2 + 1)
            window_data = data[start_idx:end_idx]
            smoothed.append(sum(window_data) / len(window_data))

        return smoothed

    def _detect_climbs(self, gps_points: List[GPSPoint]) -> List[ClimbSegment]:
        """Detect climb segments from GPS data"""
        climbs = []
        current_climb = None

        for i, point in enumerate(gps_points):
            if point.gradient_percent is None:
                continue

            # Start of a climb
            if point.gradient_percent >= self.min_climb_grade and current_climb is None:
                current_climb = {
                    "start_idx": i,
                    "start_mile": point.distance_miles,
                    "start_elevation": point.elevation_ft,
                    "max_grade": point.gradient_percent,
                    "grades": [point.gradient_percent],
                }

            # Continue climb
            elif current_climb is not None and point.gradient_percent >= 0:
                current_climb["max_grade"] = max(
                    current_climb["max_grade"], point.gradient_percent or 0
                )
                current_climb["grades"].append(point.gradient_percent or 0)

            # End of climb
            elif current_climb is not None and (
                point.gradient_percent < 0 or i == len(gps_points) - 1
            ):
                climb_length = point.distance_miles - current_climb["start_mile"]

                if climb_length >= self.min_climb_distance:
                    avg_grade = sum(current_climb["grades"]) / len(
                        current_climb["grades"]
                    )
                    elevation_gain = (
                        point.elevation_ft - current_climb["start_elevation"]
                    )

                    # Create climb segment
                    climb = ClimbSegment(
                        name=f"Climb at mile {current_climb['start_mile']:.1f}",
                        start_mile=current_climb["start_mile"],
                        length_miles=climb_length,
                        avg_grade=avg_grade,
                        max_grade=current_climb["max_grade"],
                        elevation_gain_ft=int(max(0, elevation_gain)),
                        start_coords=(
                            gps_points[current_climb["start_idx"]].latitude,
                            gps_points[current_climb["start_idx"]].longitude,
                        ),
                        end_coords=(point.latitude, point.longitude),
                        gps_points=gps_points[current_climb["start_idx"] : i + 1],
                    )

                    climbs.append(climb)
                    logger.debug(
                        f"Detected climb: {climb.name} - "
                        f"{climb.length_miles:.1f}mi at {climb.avg_grade:.1f}% avg"
                    )

                current_climb = None

        return climbs

    def _calculate_total_elevation_gain(self, gps_points: List[GPSPoint]) -> float:
        """Calculate total elevation gain from GPS points"""
        total_gain = 0.0

        for i in range(1, len(gps_points)):
            elevation_diff = gps_points[i].elevation_ft - gps_points[i - 1].elevation_ft
            if elevation_diff > 0:
                total_gain += elevation_diff

        return total_gain

    def _identify_technical_sections(self, gps_points: List[GPSPoint]) -> List[str]:
        """Identify technical sections like sharp turns or steep descents"""
        technical_sections = []

        # Look for steep descents using config parameters
        descent_threshold = self.config.descent_threshold
        min_descent_length = self.config.min_descent_length

        for i in range(len(gps_points)):
            if (
                gps_points[i].gradient_percent
                and gps_points[i].gradient_percent <= descent_threshold
            ):

                # Check if descent continues for minimum length
                start_mile = gps_points[i].distance_miles
                j = i + 1
                while (
                    j < len(gps_points)
                    and gps_points[j].gradient_percent
                    and gps_points[j].gradient_percent
                    <= self.config.descent_continuation_threshold
                ):
                    j += 1

                end_mile = gps_points[j - 1].distance_miles if j > i + 1 else start_mile
                descent_length = end_mile - start_mile
                if descent_length >= min_descent_length:
                    technical_sections.append(
                        f"Steep descent at mile {start_mile:.1f} "
                        f"({descent_length:.1f}mi, {gps_points[i].gradient_percent:.1f}% grade)"
                    )

        return technical_sections

    def _validate_coordinates(
        self, gps_points: List[GPSPoint], track_points: List
    ) -> Dict[str, int]:
        """
        Validate GPS coordinates and return validation results
        
        Args:
            gps_points: Processed GPS points with calculated distances
            track_points: Original GPX track points
            
        Returns:
            Dictionary with validation error counts
        """
        validation_results = {
            "invalid_latitude_points": 0,
            "invalid_longitude_points": 0,
            "invalid_elevation_points": 0,
            "large_distance_jumps": 0,
            "total_validation_errors": 0,
        }

        # Validate individual coordinates
        for i, (gps_point, track_point) in enumerate(zip(gps_points, track_points)):
            point_errors = self._validate_single_point(gps_point, track_point, i)
            
            # Aggregate errors
            validation_results["invalid_latitude_points"] += point_errors["invalid_latitude"]
            validation_results["invalid_longitude_points"] += point_errors["invalid_longitude"]
            validation_results["invalid_elevation_points"] += point_errors["invalid_elevation"]

        # Validate distance jumps between adjacent points
        validation_results["large_distance_jumps"] = self._validate_distance_jumps(gps_points)

        # Calculate total errors
        validation_results["total_validation_errors"] = (
            validation_results["invalid_latitude_points"] +
            validation_results["invalid_longitude_points"] +
            validation_results["invalid_elevation_points"] +
            validation_results["large_distance_jumps"]
        )

        return validation_results

    def _validate_single_point(
        self, gps_point: GPSPoint, track_point, point_index: int
    ) -> Dict[str, int]:
        """
        Validate a single GPS point
        
        Args:
            gps_point: Processed GPS point
            track_point: Original GPX track point
            point_index: Index of the point for logging
            
        Returns:
            Dictionary with error flags for this point
        """
        errors = {"invalid_latitude": 0, "invalid_longitude": 0, "invalid_elevation": 0}

        # Validate latitude
        if not self._is_coordinate_valid(
            gps_point.latitude, 
            self.config.min_latitude, 
            self.config.max_latitude
        ):
            errors["invalid_latitude"] = 1
            logger.warning(
                f"Invalid latitude at point {point_index}: {gps_point.latitude}° "
                f"(valid range: {self.config.min_latitude}° to {self.config.max_latitude}°)"
            )

        # Validate longitude
        if not self._is_coordinate_valid(
            gps_point.longitude, 
            self.config.min_longitude, 
            self.config.max_longitude
        ):
            errors["invalid_longitude"] = 1
            logger.warning(
                f"Invalid longitude at point {point_index}: {gps_point.longitude}° "
                f"(valid range: {self.config.min_longitude}° to {self.config.max_longitude}°)"
            )

        # Validate elevation (only if elevation data exists)
        if track_point.elevation is not None and not self._is_coordinate_valid(
            gps_point.elevation_ft, 
            self.config.min_elevation_ft, 
            self.config.max_elevation_ft
        ):
            errors["invalid_elevation"] = 1
            logger.warning(
                f"Invalid elevation at point {point_index}: {gps_point.elevation_ft}ft "
                f"(valid range: {self.config.min_elevation_ft}ft to {self.config.max_elevation_ft}ft)"
            )

        # Special case: Check for (0, 0) coordinates indicating GPS loss
        if (abs(gps_point.latitude) < 0.0001 and abs(gps_point.longitude) < 0.0001):
            errors["invalid_latitude"] = 1
            errors["invalid_longitude"] = 1
            logger.warning(f"GPS loss detected at point {point_index}: coordinates (0, 0)")

        return errors

    def _validate_distance_jumps(self, gps_points: List[GPSPoint]) -> int:
        """
        Validate distance jumps between adjacent GPS points
        
        Args:
            gps_points: List of GPS points with calculated distances
            
        Returns:
            Number of large distance jumps detected
        """
        large_jumps = 0

        for i in range(1, len(gps_points)):
            distance_diff = gps_points[i].distance_miles - gps_points[i - 1].distance_miles
            
            if distance_diff > self.config.max_distance_jump_miles:
                large_jumps += 1
                logger.warning(
                    f"Large distance jump detected between points {i-1} and {i}: "
                    f"{distance_diff:.3f} miles (threshold: {self.config.max_distance_jump_miles} miles)"
                )

        return large_jumps

    def _is_coordinate_valid(self, value: float, min_val: float, max_val: float) -> bool:
        """
        Check if a coordinate value is within valid bounds
        
        Args:
            value: Value to validate
            min_val: Minimum valid value
            max_val: Maximum valid value
            
        Returns:
            True if valid, False otherwise
        """
        return min_val <= value <= max_val

    def _generate_metadata(
        self, file_path: str, gps_points: List[GPSPoint], track_points: List
    ) -> GPSMetadata:
        """Generate GPS metadata for quality assessment"""
        missing_elevation = sum(1 for p in track_points if p.elevation is None)

        # Perform coordinate validation
        validation_results = self._validate_coordinates(gps_points, track_points)

        # Calculate data quality score including validation errors
        quality_score = 100.0
        if track_points:
            # Penalize for missing elevation data
            missing_ratio = missing_elevation / len(track_points)
            quality_score -= missing_ratio * self.config.quality_penalty_factor
            
            # Penalize for coordinate validation errors
            if validation_results["total_validation_errors"] > 0:
                validation_ratio = validation_results["total_validation_errors"] / len(track_points)
                quality_score -= validation_ratio * self.config.coordinate_validation_penalty
                
            # Ensure score doesn't go below 0
            quality_score = max(0, quality_score)

        # Calculate bounds
        bounds = None
        if gps_points:
            bounds = {
                "min_lat": min(p.latitude for p in gps_points),
                "max_lat": max(p.latitude for p in gps_points),
                "min_lon": min(p.longitude for p in gps_points),
                "max_lon": max(p.longitude for p in gps_points),
            }

        return GPSMetadata(
            source_file=file_path,
            total_points=len(track_points),
            missing_elevation_points=missing_elevation,
            data_quality_score=quality_score,
            smoothed=True,  # We apply smoothing by default
            parsed_at=datetime.now(),
            bounds=bounds,
            # Include validation results
            invalid_latitude_points=validation_results["invalid_latitude_points"],
            invalid_longitude_points=validation_results["invalid_longitude_points"],
            invalid_elevation_points=validation_results["invalid_elevation_points"],
            large_distance_jumps=validation_results["large_distance_jumps"],
            total_validation_errors=validation_results["total_validation_errors"],
        )
