#!/usr/bin/env python3
"""
Validation script for all course data files in the repository.

This script provides comprehensive data quality validation for all GPS course files,
both GPX examples and existing JSON course data. It generates detailed reports
showing data quality issues and recommendations for improvement.

Usage:
    python scripts/validate_all_courses.py [options]

Options:
    --format json|table|summary    Output format (default: table)
    --output PATH                  Save report to file
    --gpx-only                     Validate only GPX files
    --json-only                    Validate only JSON course files
    --min-quality FLOAT            Filter courses by minimum quality score (0.0-10.0)
    --show-valid                   Include valid courses in output
    --verbose                      Show detailed validation messages
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.gps_parser import GPSParser, GPSParserConfig
from src.utils.data_validator import DataValidator, DataQualityReport
from src.models.course import CourseProfile


class CourseValidationRunner:
    """Orchestrates validation of all course data files."""

    def __init__(self):
        self.validator = DataValidator()
        self.gps_parser = GPSParser(GPSParserConfig())
        self.results: List[Tuple[str, str, DataQualityReport]] = []

    def find_course_files(
        self, gpx_only: bool = False, json_only: bool = False
    ) -> Dict[str, List[Path]]:
        """Find all course files in the repository."""
        repo_root = Path(__file__).parent.parent

        files = {"gpx": [], "json": []}

        if not json_only:
            # Find GPX files
            gpx_dir = repo_root / "examples" / "gpx"
            if gpx_dir.exists():
                files["gpx"] = list(gpx_dir.glob("*.gpx"))

        if not gpx_only:
            # Find JSON course files
            json_dir = repo_root / "src" / "data" / "courses"
            if json_dir.exists():
                files["json"] = list(json_dir.glob("*.json"))

        return files

    def validate_gpx_file(self, gpx_path: Path) -> Tuple[str, DataQualityReport]:
        """Validate a GPX file and return its course profile and quality report."""
        try:
            course = self.gps_parser.parse_gpx_file(str(gpx_path))
            report = self.validator.validate_course(course)
            return course.name or gpx_path.stem, report
        except Exception as e:
            # Create a failed report
            from src.utils.data_validator import ValidationResult

            failed_report = DataQualityReport(
                course_name=gpx_path.stem,
                overall_score=0.0,
                total_checks=1,
                passed_checks=0,
                critical_failures=1,
                warnings=0,
                validation_results=[
                    ValidationResult(
                        check_name="GPS_PARSING",
                        passed=False,
                        message=f"Failed to parse GPX file: {str(e)}",
                        severity="critical",
                    )
                ],
            )
            return gpx_path.stem, failed_report

    def validate_json_file(self, json_path: Path) -> Tuple[str, DataQualityReport]:
        """Validate a JSON course file and return its quality report."""
        try:
            from src.utils.course_loader import load_course_from_json
            
            # Use the proper course loader to handle elevation profile conversion
            # Pass just the course name without extension and the directory
            course_name = json_path.stem  # filename without extension
            data_dir = str(json_path.parent)  # directory path
            course = load_course_from_json(course_name, data_dir)
            
            report = self.validator.validate_course(course)
            return course.name, report

        except Exception as e:
            from src.utils.data_validator import ValidationResult

            failed_report = DataQualityReport(
                course_name=json_path.stem,
                overall_score=0.0,
                total_checks=1,
                passed_checks=0,
                critical_failures=1,
                warnings=0,
                validation_results=[
                    ValidationResult(
                        check_name="JSON_PARSING",
                        passed=False,
                        message=f"Failed to parse JSON file: {str(e)}",
                        severity="critical",
                    )
                ],
            )
            return json_path.stem, failed_report

    def run_validation(
        self, gpx_only: bool = False, json_only: bool = False, verbose: bool = False
    ) -> None:
        """Run validation on all course files."""
        print("🔍 Finding course files...")
        files = self.find_course_files(gpx_only, json_only)

        total_files = len(files["gpx"]) + len(files["json"])
        if total_files == 0:
            print("❌ No course files found to validate.")
            return

        print(
            f"📊 Found {len(files['gpx'])} GPX files and {len(files['json'])} JSON files"
        )
        print("🚀 Starting validation...")
        print()

        # Validate GPX files
        for gpx_file in files["gpx"]:
            if verbose:
                print(f"  Validating GPX: {gpx_file.name}")

            course_name, report = self.validate_gpx_file(gpx_file)
            self.results.append((gpx_file.name, "GPX", report))

        # Validate JSON files
        for json_file in files["json"]:
            if verbose:
                print(f"  Validating JSON: {json_file.name}")

            course_name, report = self.validate_json_file(json_file)
            self.results.append((json_file.name, "JSON", report))

        if verbose:
            print()

    def generate_summary(self) -> Dict:
        """Generate summary statistics from validation results."""
        total_courses = len(self.results)
        valid_courses = sum(
            1 for _, _, report in self.results if report.is_valid_for_strategy
        )
        invalid_courses = total_courses - valid_courses

        total_issues = sum(
            report.total_checks - report.passed_checks for _, _, report in self.results
        )
        critical_issues = sum(report.critical_failures for _, _, report in self.results)

        avg_quality = (
            sum(report.overall_score for _, _, report in self.results) / total_courses
            if total_courses > 0
            else 0
        )

        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_courses": total_courses,
            "valid_courses": valid_courses,
            "invalid_courses": invalid_courses,
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "average_quality_score": round(avg_quality, 2),
            "validation_pass_rate": round((valid_courses / total_courses * 100), 1)
            if total_courses > 0
            else 0,
        }

    def format_table_output(
        self, show_valid: bool = False, min_quality: Optional[float] = None
    ) -> str:
        """Format results as a table."""
        if not self.results:
            return "No validation results available."

        # Filter results
        filtered_results = []
        for filename, file_type, report in self.results:
            if min_quality and report.overall_score < min_quality:
                continue
            if (
                not show_valid
                and report.is_valid_for_strategy
                and (report.total_checks - report.passed_checks) == 0
            ):
                continue
            filtered_results.append((filename, file_type, report))

        if not filtered_results:
            return "No courses match the specified criteria."

        # Build table
        lines = []
        lines.append("🏁 Course Data Validation Results")
        lines.append("=" * 80)
        lines.append("")

        # Header
        lines.append(
            f"{'File':<25} {'Type':<6} {'Quality':<8} {'Issues':<8} {'Status':<12} {'Key Issues'}"
        )
        lines.append("-" * 100)

        # Results
        for filename, file_type, report in filtered_results:
            status = "✅ Valid" if report.is_valid_for_strategy else "❌ Invalid"
            total_issues = report.total_checks - report.passed_checks
            issues_str = (
                f"{report.critical_failures}C/{total_issues}T"
                if total_issues > 0
                else "None"
            )
            quality_str = f"{report.overall_score:.1f}/100"

            # Get key issues (up to 3)
            key_issues = []
            for result in report.validation_results[:3]:
                if not result.passed:
                    check_name = result.check_name.replace("_", " ").title()
                    key_issues.append(f"{check_name}")

            key_issues_str = ", ".join(key_issues[:3])
            if len(report.validation_results) > 3:
                key_issues_str += "..."

            lines.append(
                f"{filename:<25} {file_type:<6} {quality_str:<8} {issues_str:<8} {status:<12} {key_issues_str}"
            )

        lines.append("")

        # Summary
        summary = self.generate_summary()
        lines.append("📊 Summary:")
        lines.append(f"  • Total courses: {summary['total_courses']}")
        lines.append(
            f"  • Valid courses: {summary['valid_courses']} ({summary['validation_pass_rate']}%)"
        )
        lines.append(
            f"  • Total issues: {summary['total_issues']} ({summary['critical_issues']} critical)"
        )
        lines.append(f"  • Average quality: {summary['average_quality_score']}/100")

        return "\n".join(lines)

    def format_json_output(
        self, show_valid: bool = False, min_quality: Optional[float] = None
    ) -> str:
        """Format results as JSON."""
        # Filter results
        filtered_results = []
        for filename, file_type, report in self.results:
            if min_quality and report.overall_score < min_quality:
                continue
            total_issues = report.total_checks - report.passed_checks
            if not show_valid and report.is_valid_for_strategy and total_issues == 0:
                continue

            # Convert report to dict
            result_dict = {
                "filename": filename,
                "file_type": file_type,
                "course_name": report.course_name,
                "is_valid": report.is_valid_for_strategy,
                "quality_score": report.overall_score,
                "total_issues": total_issues,
                "critical_issues": report.critical_failures,
                "validation_results": [
                    {
                        "check_name": result.check_name,
                        "passed": result.passed,
                        "message": result.message,
                        "severity": result.severity,
                        "details": result.details,
                    }
                    for result in report.validation_results
                ],
            }
            filtered_results.append(result_dict)

        output = {"summary": self.generate_summary(), "results": filtered_results}

        return json.dumps(output, indent=2)

    def format_summary_output(self) -> str:
        """Format results as a brief summary."""
        if not self.results:
            return "No validation results available."

        summary = self.generate_summary()

        lines = []
        lines.append("🏁 Course Data Validation Summary")
        lines.append("=" * 40)
        lines.append(f"Courses Analyzed: {summary['total_courses']}")
        lines.append(f"Validation Pass Rate: {summary['validation_pass_rate']}%")
        lines.append(f"Average Quality Score: {summary['average_quality_score']}/100")
        lines.append("")

        if summary["invalid_courses"] > 0:
            lines.append(f"⚠️  {summary['invalid_courses']} courses need attention")
            lines.append(f"   {summary['critical_issues']} critical issues found")
        else:
            lines.append("✅ All courses passed validation!")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Validate all course data files in the repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/validate_all_courses.py
  python scripts/validate_all_courses.py --format json --output report.json
  python scripts/validate_all_courses.py --gpx-only --min-quality 7.0
  python scripts/validate_all_courses.py --format summary --show-valid
        """,
    )

    parser.add_argument(
        "--format",
        choices=["json", "table", "summary"],
        default="table",
        help="Output format (default: table)",
    )

    parser.add_argument("--output", type=str, help="Save report to file")

    parser.add_argument(
        "--gpx-only", action="store_true", help="Validate only GPX files"
    )

    parser.add_argument(
        "--json-only", action="store_true", help="Validate only JSON course files"
    )

    parser.add_argument(
        "--min-quality",
        type=float,
        help="Filter courses by minimum quality score (0.0-10.0)",
    )

    parser.add_argument(
        "--show-valid", action="store_true", help="Include valid courses in output"
    )

    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed validation messages"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.gpx_only and args.json_only:
        print("❌ Error: Cannot specify both --gpx-only and --json-only")
        sys.exit(1)

    if args.min_quality is not None and (args.min_quality < 0 or args.min_quality > 10):
        print("❌ Error: --min-quality must be between 0.0 and 10.0")
        sys.exit(1)

    # Run validation
    try:
        runner = CourseValidationRunner()
        runner.run_validation(
            gpx_only=args.gpx_only, json_only=args.json_only, verbose=args.verbose
        )

        # Generate output
        if args.format == "json":
            output = runner.format_json_output(
                show_valid=args.show_valid, min_quality=args.min_quality
            )
        elif args.format == "summary":
            output = runner.format_summary_output()
        else:  # table
            output = runner.format_table_output(
                show_valid=args.show_valid, min_quality=args.min_quality
            )

        # Output results
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"✅ Report saved to {args.output}")
        else:
            print(output)

    except KeyboardInterrupt:
        print("\n❌ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during validation: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
