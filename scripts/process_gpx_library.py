#!/usr/bin/env python3
"""
Process GPX Library - Convert all GPX files in data directory to course JSON files

This script processes a library of GPX files and converts them to standardized
course JSON format for the race strategy optimizer.
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.utils.gps_parser import GPSParser
from src.models.course import CourseProfile


def get_course_info(gpx_filename: str) -> Dict[str, str]:
    """
    Get course-specific information based on GPX filename
    
    Args:
        gpx_filename: Name of the GPX file
        
    Returns:
        Dictionary with course-specific metadata
    """
    course_configs = {
        "alpedhuez_triathlon.gpx": {
            "name": "Alpe d'Huez Triathlon L",
            "location": "French Alps, France",
            "altitude_ft": 6000,
            "swim_venue": "Lac du Verney", 
            "swim_type": "Mountain lake",
            "typical_water_temp_f": 59,
            "bike_profile": "Extreme mountain",
            "run_profile": "Three loops at altitude",
            "run_surface": "Mixed trail and road at 1800m altitude",
            "surface_types": ["Mountain asphalt", "Some rough sections"],
            "swim_distance_miles": 1.37,
            "run_distance_miles": 11.8,
            "run_elevation_gain_ft": 360,
            "notes": "High altitude effects (1800m+), famous 21 switchbacks"
        },
        "im70.3_pennstate.gpx": {
            "name": "Ironman 70.3 Happy Valley (GPS)",
            "location": "Pennsylvania, USA",
            "altitude_ft": 1200,
            "swim_venue": "Foster Joseph Sayers Lake",
            "swim_type": "Lake swim", 
            "typical_water_temp_f": 68,
            "bike_profile": "Rolling to hilly with major climbs",
            "run_profile": "Two loops with hills",
            "run_surface": "Mixed road and wide pedestrian paths",
            "surface_types": ["Asphalt", "Some rough road sections"],
            "swim_distance_miles": 1.2,
            "run_distance_miles": 13.1,
            "run_elevation_gain_ft": 206,
            "notes": "Point-to-point course with dual transitions"
        }
    }
    
    return course_configs.get(gpx_filename, {
        "name": Path(gpx_filename).stem.replace("_", " ").title(),
        "location": "Unknown",
        "altitude_ft": 0,
        "swim_venue": "Unknown",
        "swim_type": "Unknown",
        "typical_water_temp_f": 68,
        "bike_profile": "Unknown",
        "run_profile": "Unknown", 
        "run_surface": "Unknown",
        "surface_types": ["Unknown"],
        "swim_distance_miles": 1.2,
        "run_distance_miles": 13.1,
        "run_elevation_gain_ft": 200,
        "notes": "Processed from GPX file"
    })


def course_profile_to_json_dict(course_profile: CourseProfile, course_info: Dict) -> dict:
    """
    Convert CourseProfile to JSON-serializable dictionary with course-specific metadata
    
    Args:
        course_profile: CourseProfile object
        course_info: Course-specific metadata
    
    Returns:
        Dictionary representation suitable for JSON serialization
    """
    # Convert ClimbSegment objects to dictionaries
    key_climbs = []
    for climb in course_profile.key_climbs:
        key_climbs.append({
            "name": climb.name,
            "start_mile": climb.start_mile,
            "length_miles": climb.length_miles,
            "avg_grade": climb.avg_grade,
            "max_grade": climb.max_grade,
            "elevation_gain_ft": climb.elevation_gain_ft
        })

    return {
        "name": course_info.get("name", course_profile.name),
        "location": course_info.get("location", "Unknown"),
        "bike_distance_miles": course_profile.bike_distance_miles,
        "bike_elevation_gain_ft": course_profile.bike_elevation_gain_ft,
        "swim_distance_miles": course_info.get("swim_distance_miles", 1.2),
        "run_distance_miles": course_info.get("run_distance_miles", 13.1),
        "run_elevation_gain_ft": course_info.get("run_elevation_gain_ft", 200),
        "altitude_ft": course_info.get("altitude_ft", 0),
        "key_climbs": key_climbs,
        "technical_sections": course_profile.technical_sections,
        "surface_types": course_info.get("surface_types", ["Asphalt"]),
        "race_details": {
            "swim_venue": course_info.get("swim_venue", "Unknown"),
            "swim_type": course_info.get("swim_type", "Unknown"),
            "wetsuit_legal": True,
            "typical_water_temp_f": course_info.get("typical_water_temp_f", 68),
            "bike_profile": course_info.get("bike_profile", "Unknown"),
            "run_profile": course_info.get("run_profile", "Unknown"),
            "run_surface": course_info.get("run_surface", "Unknown")
        },
        "data_source": {
            "type": "GPS Track",
            "source": "Local GPX file",
            "gpx_file": course_profile.gps_metadata.source_file if course_profile.gps_metadata else "Unknown",
            "data_quality_score": course_profile.gps_metadata.data_quality_score if course_profile.gps_metadata else None,
            "total_gps_points": course_profile.gps_metadata.total_points if course_profile.gps_metadata else None,
            "parsed_at": course_profile.gps_metadata.parsed_at.isoformat() if course_profile.gps_metadata else None
        },
        "notes": course_info.get("notes", "")
    }


def save_course_json(course_dict: dict, output_path: str):
    """
    Save course dictionary to JSON file with pretty formatting
    
    Args:
        course_dict: Course data dictionary
        output_path: Path to save JSON file
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(course_dict, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Course JSON saved to: {output_path}")


def process_gpx_file(gpx_path: Path, output_dir: Path) -> bool:
    """
    Process a single GPX file and create corresponding course JSON
    
    Args:
        gpx_path: Path to GPX file
        output_dir: Directory to save course JSON
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"\n🔍 Processing: {gpx_path.name}")
        
        # Get course-specific information
        course_info = get_course_info(gpx_path.name)
        
        # Parse GPX file
        parser = GPSParser()
        course_profile = parser.parse_gpx_file(str(gpx_path))
        
        # Override course name with configured name
        course_profile.name = course_info.get("name", course_profile.name)
        
        print(f"   📊 Course: {course_profile.name}")
        print(f"   🚴 Distance: {course_profile.bike_distance_miles:.1f} miles")  
        print(f"   ⛰️  Elevation: {course_profile.bike_elevation_gain_ft} ft")
        print(f"   🧗 Key Climbs: {len(course_profile.key_climbs)}")
        
        # Convert to JSON format
        course_dict = course_profile_to_json_dict(course_profile, course_info)
        
        # Generate output filename (replace .gpx with .json, normalize name)
        json_filename = gpx_path.stem.lower().replace(" ", "_") + ".json"
        json_path = output_dir / json_filename
        
        # Save course JSON
        save_course_json(course_dict, str(json_path))
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error processing {gpx_path.name}: {e}")
        return False


def process_gpx_library(data_dir: str = None, output_dir: str = None) -> List[str]:
    """
    Process all GPX files in the data directory
    
    Args:
        data_dir: Directory containing GPX files (default: ./data)
        output_dir: Directory to save course JSON files (default: ./src/data/courses)
        
    Returns:
        List of successfully processed course names
    """
    # Set default paths
    project_root = Path(__file__).parent.parent
    data_path = Path(data_dir) if data_dir else project_root / "data"
    output_path = Path(output_dir) if output_dir else project_root / "src" / "data" / "courses"
    
    print(f"🚴‍♂️ GPX Library Processor")
    print("=" * 40)
    print(f"📂 Data directory: {data_path}")
    print(f"💾 Output directory: {output_path}")
    
    # Find all GPX files
    gpx_files = list(data_path.glob("*.gpx"))
    
    if not gpx_files:
        print(f"\n❌ No GPX files found in {data_path}")
        return []
    
    print(f"\n📋 Found {len(gpx_files)} GPX file(s):")
    for gpx_file in gpx_files:
        print(f"   - {gpx_file.name}")
    
    # Process each GPX file
    processed_courses = []
    successful = 0
    failed = 0
    
    for gpx_file in gpx_files:
        if process_gpx_file(gpx_file, output_path):
            processed_courses.append(gpx_file.stem.lower().replace(" ", "_"))
            successful += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n📊 Processing Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📁 Course JSON files created: {len(processed_courses)}")
    
    if processed_courses:
        print(f"\n🎯 Available courses:")
        for course in processed_courses:
            print(f"   - {course}")
    
    return processed_courses


def main():
    """Main function"""
    try:
        processed_courses = process_gpx_library()
        
        if processed_courses:
            print(f"\n🎉 Successfully processed {len(processed_courses)} course(s)!")
            print("You can now load them using:")
            for course in processed_courses:
                print(f"   load_course_from_json('{course}')")
        else:
            print(f"\n💥 No courses were processed successfully")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())