# src/utils/data_validator.py
"""
Comprehensive data validation system for GPS course data.

Ensures GPS course data is accurate and complete before use in race strategy generation.
Validates elevation profiles, gradient calculations, climb detection, and overall data quality.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..models.course import CourseProfile

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Container for a single validation check result."""

    check_name: str
    passed: bool
    severity: str  # 'critical', 'warning', 'info'
    message: str
    details: Optional[Dict[str, Any]] = None
    suggested_fix: Optional[str] = None


@dataclass
class DataQualityReport:
    """Comprehensive data quality assessment report."""

    course_name: str
    overall_score: float  # 0-100
    total_checks: int
    passed_checks: int
    critical_failures: int
    warnings: int
    validation_results: List[ValidationResult] = field(default_factory=list)

    @property
    def is_valid_for_strategy(self) -> bool:
        """Determine if course data is valid enough for race strategy generation."""
        return self.critical_failures == 0 and self.overall_score >= 75.0

    @property
    def quality_rating(self) -> str:
        """Human-readable quality rating."""
        if self.overall_score >= 95:
            return "Excellent"
        elif self.overall_score >= 85:
            return "Good"
        elif self.overall_score >= 75:
            return "Acceptable"
        elif self.overall_score >= 60:
            return "Poor"
        else:
            return "Unusable"


class DataValidator:
    """Comprehensive GPS course data validation system."""

    # Physical constraints for validation
    MAX_REASONABLE_GRADIENT = 35.0  # Maximum realistic road gradient (%)
    MAX_ELEVATION_GAIN_PER_MILE = 1500  # Feet per mile maximum
    MIN_COURSE_DISTANCE = 5.0  # Minimum reasonable course distance (miles)
    MAX_COURSE_DISTANCE = 200.0  # Maximum reasonable course distance (miles)
    MAX_ELEVATION_FT = 29000  # Maximum reasonable elevation (Mt. Everest)
    MIN_ELEVATION_FT = -500  # Minimum reasonable elevation (below sea level)
    MAX_DISTANCE_JUMP_THRESHOLD = 2.0  # Max distance between GPS points (miles)
    MIN_GPS_POINTS = 10  # Minimum GPS points for valid course

    def __init__(self):
        """Initialize the data validator."""
        self.validation_checks = [
            self._validate_basic_course_data,
            self._validate_distance_bounds,
            self._validate_elevation_data,
            self._validate_gradient_calculations,
            self._validate_climb_detection,
            self._validate_gps_point_quality,
            self._validate_course_consistency,
            self._validate_technical_sections,
        ]

    def validate_course(self, course: CourseProfile) -> DataQualityReport:
        """
        Perform comprehensive validation of course data.

        Args:
            course: CourseProfile to validate

        Returns:
            DataQualityReport with detailed validation results
        """
        report = DataQualityReport(
            course_name=course.name or "Unknown Course",
            overall_score=0.0,
            total_checks=0,
            passed_checks=0,
            critical_failures=0,
            warnings=0,
        )

        # Run all validation checks
        for validation_check in self.validation_checks:
            try:
                results = validation_check(course)
                if not isinstance(results, list):
                    results = [results]

                report.validation_results.extend(results)

            except Exception as e:
                error_result = ValidationResult(
                    check_name=validation_check.__name__,
                    passed=False,
                    severity="critical",
                    message=f"Validation check failed with error: {e}",
                    suggested_fix="Review course data structure and fix data corruption",
                )
                report.validation_results.append(error_result)

        # Calculate overall scores
        report.total_checks = len(report.validation_results)
        report.passed_checks = sum(1 for r in report.validation_results if r.passed)
        report.critical_failures = sum(
            1
            for r in report.validation_results
            if not r.passed and r.severity == "critical"
        )
        report.warnings = sum(
            1
            for r in report.validation_results
            if not r.passed and r.severity == "warning"
        )

        # Calculate weighted score (critical failures heavily penalized)
        if report.total_checks > 0:
            base_score = (report.passed_checks / report.total_checks) * 100
            critical_penalty = report.critical_failures * 20
            warning_penalty = report.warnings * 5
            report.overall_score = max(
                0, base_score - critical_penalty - warning_penalty
            )

        return report

    def _validate_basic_course_data(self, course: CourseProfile) -> ValidationResult:
        """Validate basic course structure and required fields."""
        errors = []

        if not course.name or len(course.name.strip()) == 0:
            errors.append("Course name is missing or empty")

        if course.bike_distance_miles <= 0:
            errors.append(f"Invalid bike distance: {course.bike_distance_miles}")

        if course.bike_elevation_gain_ft < 0:
            errors.append(f"Negative elevation gain: {course.bike_elevation_gain_ft}")

        if errors:
            return ValidationResult(
                check_name="Basic Course Data",
                passed=False,
                severity="critical",
                message=f"Basic course data validation failed: {'; '.join(errors)}",
                suggested_fix="Ensure course has valid name, distance, and elevation data",
            )

        return ValidationResult(
            check_name="Basic Course Data",
            passed=True,
            severity="info",
            message="All basic course data fields are valid",
        )

    def _validate_distance_bounds(self, course: CourseProfile) -> ValidationResult:
        """Validate course distance is within reasonable bounds."""
        distance = course.bike_distance_miles

        if distance < self.MIN_COURSE_DISTANCE:
            return ValidationResult(
                check_name="Distance Bounds",
                passed=False,
                severity="critical",
                message=f"Course distance {distance:.1f} miles is unreasonably short (min: {self.MIN_COURSE_DISTANCE})",
                suggested_fix="Check GPS data for missing segments or incorrect units",
            )

        if distance > self.MAX_COURSE_DISTANCE:
            return ValidationResult(
                check_name="Distance Bounds",
                passed=False,
                severity="critical",
                message=f"Course distance {distance:.1f} miles is unreasonably long (max: {self.MAX_COURSE_DISTANCE})",
                details={
                    "actual_distance": distance,
                    "max_allowed": self.MAX_COURSE_DISTANCE,
                },
                suggested_fix="Check for GPS errors causing inflated distance calculations",
            )

        return ValidationResult(
            check_name="Distance Bounds",
            passed=True,
            severity="info",
            message=f"Course distance {distance:.1f} miles is within reasonable bounds",
        )

    def _validate_elevation_data(self, course: CourseProfile) -> List[ValidationResult]:
        """Validate elevation data quality and bounds."""
        results = []

        # Check elevation profile exists
        if not course.elevation_profile or len(course.elevation_profile) == 0:
            results.append(
                ValidationResult(
                    check_name="Elevation Profile",
                    passed=False,
                    severity="critical",
                    message="No elevation profile data available",
                    suggested_fix="Ensure GPX file contains elevation data for all track points",
                )
            )
            return results

        # Analyze elevation values
        elevations = [
            point.elevation_ft
            for point in course.elevation_profile
            if point.elevation_ft is not None
        ]

        if not elevations:
            results.append(
                ValidationResult(
                    check_name="Elevation Values",
                    passed=False,
                    severity="critical",
                    message="No valid elevation values found in elevation profile",
                    suggested_fix="Check GPX file for elevation data corruption",
                )
            )
            return results

        # Check elevation bounds
        min_elev = min(elevations)
        max_elev = max(elevations)
        invalid_elevations = [
            e
            for e in elevations
            if e < self.MIN_ELEVATION_FT or e > self.MAX_ELEVATION_FT
        ]

        if invalid_elevations:
            results.append(
                ValidationResult(
                    check_name="Elevation Bounds",
                    passed=False,
                    severity="warning",
                    message=f"Found {len(invalid_elevations)} elevation values outside reasonable bounds",
                    details={
                        "min_elevation": min_elev,
                        "max_elevation": max_elev,
                        "invalid_count": len(invalid_elevations),
                        "bounds": f"{self.MIN_ELEVATION_FT}-{self.MAX_ELEVATION_FT}ft",
                    },
                    suggested_fix="Review GPS data for elevation sensor errors",
                )
            )
        else:
            results.append(
                ValidationResult(
                    check_name="Elevation Bounds",
                    passed=True,
                    severity="info",
                    message=f"All elevation values within reasonable bounds ({min_elev:.0f}-{max_elev:.0f}ft)",
                )
            )

        # Check elevation gain reasonableness
        total_gain = course.bike_elevation_gain_ft
        distance = course.bike_distance_miles
        gain_per_mile = total_gain / distance if distance > 0 else 0

        if gain_per_mile > self.MAX_ELEVATION_GAIN_PER_MILE:
            results.append(
                ValidationResult(
                    check_name="Elevation Gain Rate",
                    passed=False,
                    severity="warning",
                    message=f"Elevation gain rate {gain_per_mile:.0f} ft/mile exceeds maximum reasonable rate",
                    details={
                        "gain_per_mile": gain_per_mile,
                        "max_reasonable": self.MAX_ELEVATION_GAIN_PER_MILE,
                        "total_gain": total_gain,
                        "distance": distance,
                    },
                    suggested_fix="Verify elevation data accuracy or check for GPS errors",
                )
            )
        else:
            results.append(
                ValidationResult(
                    check_name="Elevation Gain Rate",
                    passed=True,
                    severity="info",
                    message=f"Elevation gain rate {gain_per_mile:.0f} ft/mile is reasonable",
                )
            )

        return results

    def _validate_gradient_calculations(
        self, course: CourseProfile
    ) -> List[ValidationResult]:
        """Validate gradient calculations and detect impossible slopes."""
        results = []

        if not course.key_climbs:
            results.append(
                ValidationResult(
                    check_name="Gradient Calculations",
                    passed=True,
                    severity="info",
                    message="No climbs detected, gradient validation skipped",
                )
            )
            return results

        extreme_gradients = []
        impossible_gradients = []

        for climb in course.key_climbs:
            if climb.max_grade > self.MAX_REASONABLE_GRADIENT:
                if climb.max_grade > 50.0:  # Physically impossible for roads
                    impossible_gradients.append((climb.name, climb.max_grade))
                else:
                    extreme_gradients.append((climb.name, climb.max_grade))

        if impossible_gradients:
            results.append(
                ValidationResult(
                    check_name="Impossible Gradients",
                    passed=False,
                    severity="critical",
                    message=f"Found {len(impossible_gradients)} climbs with impossible gradients (>50%)",
                    details={
                        "impossible_gradients": impossible_gradients,
                        "max_reasonable": self.MAX_REASONABLE_GRADIENT,
                    },
                    suggested_fix="Check elevation data for GPS errors or calculation bugs",
                )
            )

        if extreme_gradients:
            results.append(
                ValidationResult(
                    check_name="Extreme Gradients",
                    passed=False,
                    severity="warning",
                    message=f"Found {len(extreme_gradients)} climbs with extreme gradients (>{self.MAX_REASONABLE_GRADIENT}%)",
                    details={
                        "extreme_gradients": extreme_gradients,
                        "max_reasonable": self.MAX_REASONABLE_GRADIENT,
                    },
                    suggested_fix="Verify if these extreme gradients are accurate for the course",
                )
            )

        if not extreme_gradients and not impossible_gradients:
            max_gradient = max(climb.max_grade for climb in course.key_climbs)
            results.append(
                ValidationResult(
                    check_name="Gradient Calculations",
                    passed=True,
                    severity="info",
                    message=f"All gradients are reasonable (max: {max_gradient:.1f}%)",
                )
            )

        return results

    def _validate_climb_detection(self, course: CourseProfile) -> ValidationResult:
        """Validate climb detection accuracy and completeness."""
        if not course.key_climbs:
            # Check if course should have climbs based on elevation gain
            distance = course.bike_distance_miles
            gain = course.bike_elevation_gain_ft
            gain_per_mile = gain / distance if distance > 0 else 0

            if gain_per_mile > 100:  # Should probably have detected some climbs
                return ValidationResult(
                    check_name="Climb Detection",
                    passed=False,
                    severity="warning",
                    message=f"No climbs detected despite {gain_per_mile:.0f} ft/mile elevation gain",
                    details={"elevation_gain_per_mile": gain_per_mile},
                    suggested_fix="Review climb detection parameters or elevation data quality",
                )
            else:
                return ValidationResult(
                    check_name="Climb Detection",
                    passed=True,
                    severity="info",
                    message="No climbs detected, which is reasonable for this elevation profile",
                )

        # Validate climb characteristics
        invalid_climbs = []
        for climb in course.key_climbs:
            if climb.length_miles <= 0:
                invalid_climbs.append(f"{climb.name}: zero/negative length")
            if climb.elevation_gain_ft <= 0:
                invalid_climbs.append(f"{climb.name}: zero/negative elevation gain")
            if climb.avg_grade <= 0:
                invalid_climbs.append(f"{climb.name}: zero/negative average grade")

        if invalid_climbs:
            return ValidationResult(
                check_name="Climb Detection",
                passed=False,
                severity="critical",
                message=f"Detected invalid climb characteristics: {'; '.join(invalid_climbs[:3])}",
                details={"invalid_climbs": len(invalid_climbs)},
                suggested_fix="Review climb detection algorithm and elevation data",
            )

        return ValidationResult(
            check_name="Climb Detection",
            passed=True,
            severity="info",
            message=f"Detected {len(course.key_climbs)} valid climbs with reasonable characteristics",
        )

    def _validate_gps_point_quality(
        self, course: CourseProfile
    ) -> List[ValidationResult]:
        """Validate GPS point data quality and consistency."""
        results = []

        if not course.elevation_profile:
            results.append(
                ValidationResult(
                    check_name="GPS Point Quality",
                    passed=False,
                    severity="critical",
                    message="No GPS elevation profile available for quality assessment",
                    suggested_fix="Ensure GPX file contains track points with coordinates",
                )
            )
            return results

        # Check minimum number of GPS points
        point_count = len(course.elevation_profile)
        if point_count < self.MIN_GPS_POINTS:
            results.append(
                ValidationResult(
                    check_name="GPS Point Count",
                    passed=False,
                    severity="critical",
                    message=f"Insufficient GPS points: {point_count} (minimum: {self.MIN_GPS_POINTS})",
                    suggested_fix="Ensure GPX file contains adequate track point density",
                )
            )
            return results

        # Check for large distance jumps
        large_jumps = []
        if hasattr(course, "gps_metadata") and course.gps_metadata:
            if hasattr(course.gps_metadata, "large_distance_jumps"):
                jump_count = course.gps_metadata.large_distance_jumps
                if jump_count > 0:
                    large_jumps_per_mile = jump_count / course.bike_distance_miles

                    if large_jumps_per_mile > 0.5:  # More than 1 jump per 2 miles
                        results.append(
                            ValidationResult(
                                check_name="GPS Point Continuity",
                                passed=False,
                                severity="warning",
                                message=f"High number of large distance jumps: {jump_count} ({large_jumps_per_mile:.1f} per mile)",
                                details={
                                    "jump_count": jump_count,
                                    "jumps_per_mile": large_jumps_per_mile,
                                },
                                suggested_fix="Review GPS track for signal loss or tracking errors",
                            )
                        )
                    else:
                        results.append(
                            ValidationResult(
                                check_name="GPS Point Continuity",
                                passed=True,
                                severity="info",
                                message=f"Acceptable number of distance jumps: {jump_count}",
                            )
                        )

        results.append(
            ValidationResult(
                check_name="GPS Point Count",
                passed=True,
                severity="info",
                message=f"Adequate GPS point density: {point_count} points",
            )
        )

        return results

    def _validate_course_consistency(
        self, course: CourseProfile
    ) -> List[ValidationResult]:
        """Validate internal consistency of course data."""
        results = []

        # Check if total elevation gain matches climb elevation gains
        if course.key_climbs:
            climb_total_gain = sum(
                climb.elevation_gain_ft for climb in course.key_climbs
            )
            course_total_gain = course.bike_elevation_gain_ft

            # Allow for some discrepancy due to descents and undetected climbs
            if climb_total_gain > course_total_gain * 1.5:
                results.append(
                    ValidationResult(
                        check_name="Elevation Consistency",
                        passed=False,
                        severity="warning",
                        message=f"Climb elevation gains ({climb_total_gain:.0f}ft) significantly exceed total course gain ({course_total_gain:.0f}ft)",
                        details={
                            "climb_total": climb_total_gain,
                            "course_total": course_total_gain,
                            "ratio": (
                                climb_total_gain / course_total_gain
                                if course_total_gain > 0
                                else float("inf")
                            ),
                        },
                        suggested_fix="Review climb detection algorithm or elevation calculations",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="Elevation Consistency",
                        passed=True,
                        severity="info",
                        message="Climb elevation gains are consistent with total course elevation",
                    )
                )

        # Check coordinate bounds if available
        if course.start_coords and course.finish_coords:
            start_lat, start_lon = course.start_coords
            finish_lat, finish_lon = course.finish_coords

            # Basic coordinate validation
            if not (-90 <= start_lat <= 90) or not (-180 <= start_lon <= 180):
                results.append(
                    ValidationResult(
                        check_name="Coordinate Bounds",
                        passed=False,
                        severity="critical",
                        message=f"Invalid start coordinates: {start_lat}, {start_lon}",
                        suggested_fix="Check GPS data for coordinate corruption",
                    )
                )
            elif not (-90 <= finish_lat <= 90) or not (-180 <= finish_lon <= 180):
                results.append(
                    ValidationResult(
                        check_name="Coordinate Bounds",
                        passed=False,
                        severity="critical",
                        message=f"Invalid finish coordinates: {finish_lat}, {finish_lon}",
                        suggested_fix="Check GPS data for coordinate corruption",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="Coordinate Bounds",
                        passed=True,
                        severity="info",
                        message="Start and finish coordinates are within valid ranges",
                    )
                )

        return results

    def _validate_technical_sections(self, course: CourseProfile) -> ValidationResult:
        """Validate identification of technical sections."""
        # This is a placeholder for future technical section validation
        # Currently we don't have specific technical section detection
        return ValidationResult(
            check_name="Technical Sections",
            passed=True,
            severity="info",
            message="Technical section validation not implemented yet",
            details={"feature_status": "future_enhancement"},
            suggested_fix="Implement technical section detection algorithm",
        )


def generate_quality_report_summary(report: DataQualityReport) -> str:
    """Generate a human-readable summary of the data quality report."""
    summary_lines = [
        f"📊 DATA QUALITY REPORT: {report.course_name}",
        "=" * 60,
        f"Overall Score: {report.overall_score:.1f}/100 ({report.quality_rating})",
        f"Validation Status: {'✅ VALID' if report.is_valid_for_strategy else '❌ INVALID'} for race strategy",
        "",
        "Results Summary:",
        f"  • Total Checks: {report.total_checks}",
        f"  • Passed: {report.passed_checks}",
        f"  • Critical Failures: {report.critical_failures}",
        f"  • Warnings: {report.warnings}",
        "",
        "Detailed Results:",
    ]

    for result in report.validation_results:
        status_icon = (
            "✅" if result.passed else ("🚨" if result.severity == "critical" else "⚠️")
        )
        summary_lines.append(f"  {status_icon} {result.check_name}: {result.message}")

        if result.suggested_fix and not result.passed:
            summary_lines.append(f"     💡 Fix: {result.suggested_fix}")

    if report.critical_failures > 0:
        summary_lines.extend(
            [
                "",
                "🚨 CRITICAL ISSUES DETECTED:",
                "This course data has critical quality issues that must be resolved",
                "before it can be used for race strategy generation.",
            ]
        )
    elif report.warnings > 0:
        summary_lines.extend(
            [
                "",
                "⚠️  DATA QUALITY WARNINGS:",
                "This course data has some quality issues but can still be used",
                "for strategy generation with reduced confidence.",
            ]
        )
    else:
        summary_lines.extend(
            [
                "",
                "🎉 EXCELLENT DATA QUALITY:",
                "This course data passes all validation checks and is ready",
                "for high-confidence race strategy generation.",
            ]
        )

    return "\n".join(summary_lines)
