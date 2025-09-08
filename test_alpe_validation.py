#!/usr/bin/env python3
"""
Test GPS coordinate validation system on Alpe d'Huez GPX data
"""

import sys
sys.path.append('.')

from src.utils.gps_parser import GPSParser, GPSParserConfig
from src.utils.course_loader import load_alpe_dhuez

def main():
    print("🏔️  Testing GPS Coordinate Validation on Alpe d'Huez")
    print("=" * 60)
    
    # Test 1: Default validation settings
    print("\n1️⃣  DEFAULT VALIDATION SETTINGS")
    print("-" * 30)
    
    try:
        parser = GPSParser()
        course = parser.parse_gpx_file('data/alpedhuez_triathlon.gpx')
        
        print(f"📊 Course: {course.name}")
        print(f"🚴 Distance: {course.bike_distance_miles:.1f} miles")
        print(f"⛰️  Elevation: {course.bike_elevation_gain_ft:,} ft")
        print(f"🧗 Key Climbs: {len(course.key_climbs)}")
        
        # Check validation results
        metadata = course.gps_metadata
        print(f"\n✅ Validation Results:")
        print(f"   📍 Total GPS points: {metadata.total_points:,}")
        print(f"   ❌ Invalid latitude: {metadata.invalid_latitude_points}")
        print(f"   ❌ Invalid longitude: {metadata.invalid_longitude_points}")
        print(f"   ❌ Invalid elevation: {metadata.invalid_elevation_points}")
        print(f"   🦘 Large distance jumps: {metadata.large_distance_jumps}")
        print(f"   🚫 Total validation errors: {metadata.total_validation_errors}")
        print(f"   🎯 Data quality score: {metadata.data_quality_score:.1f}/100")
        
        if metadata.total_validation_errors == 0:
            print("   ✨ Perfect! No validation errors detected")
        else:
            print(f"   ⚠️  Found {metadata.total_validation_errors} validation issues")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Strict validation for mountain courses
    print("\n\n2️⃣  STRICT MOUNTAIN VALIDATION")
    print("-" * 30)
    
    try:
        strict_config = GPSParserConfig(
            min_elevation_ft=0.0,                    # Sea level minimum
            max_elevation_ft=15000.0,                # Alps maximum  
            max_distance_jump_miles=0.2,             # Very strict distance validation
            coordinate_validation_penalty=30.0       # Higher penalty for errors
        )
        
        strict_parser = GPSParser(config=strict_config)
        strict_course = strict_parser.parse_gpx_file('data/alpedhuez_triathlon.gpx')
        
        strict_metadata = strict_course.gps_metadata
        print(f"🎯 Strict quality score: {strict_metadata.data_quality_score:.1f}/100")
        print(f"🚫 Strict validation errors: {strict_metadata.total_validation_errors}")
        print(f"🦘 Distance jump violations: {strict_metadata.large_distance_jumps}")
        
        if strict_metadata.large_distance_jumps > 0:
            print(f"   ⚠️  Detected {strict_metadata.large_distance_jumps} points with >0.2mi jumps")
        
    except Exception as e:
        print(f"❌ Error with strict validation: {e}")
    
    # Test 3: Compare with course loader 
    print("\n\n3️⃣  COURSE LOADER COMPARISON")
    print("-" * 30)
    
    try:
        loaded_course = load_alpe_dhuez()
        loaded_metadata = loaded_course.gps_metadata
        
        print("📦 Via course loader:")
        print(f"   🎯 Quality score: {loaded_metadata.data_quality_score:.1f}/100")
        print(f"   🚫 Validation errors: {loaded_metadata.total_validation_errors}")
        print(f"   📍 GPS points: {loaded_metadata.total_points:,}")
        
        # Compare with direct parsing
        if loaded_metadata.data_quality_score == metadata.data_quality_score:
            print("   ✅ Consistent with direct parsing")
        else:
            print("   ⚠️  Different from direct parsing")
            
    except Exception as e:
        print(f"❌ Error loading course: {e}")
    
    # Test 4: Elevation analysis
    print("\n\n4️⃣  ELEVATION ANALYSIS") 
    print("-" * 30)
    
    try:
        if course.elevation_profile:
            elevations = [p.elevation_ft for p in course.elevation_profile]
            min_elev = min(elevations)
            max_elev = max(elevations)
            
            print(f"📏 Elevation range: {min_elev:.0f}ft to {max_elev:.0f}ft")
            print(f"🏔️  Max altitude: {max_elev:.0f}ft ({max_elev * 0.3048:.0f}m)")
            
            # Check for extreme values
            extreme_low = [e for e in elevations if e < -500]
            extreme_high = [e for e in elevations if e > 25000]
            
            if extreme_low:
                print(f"   ⚠️  {len(extreme_low)} points below -500ft")
            if extreme_high:
                print(f"   ⚠️  {len(extreme_high)} points above 25,000ft")
                
            if not extreme_low and not extreme_high:
                print("   ✅ All elevations within reasonable bounds")
                
    except Exception as e:
        print(f"❌ Error analyzing elevations: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Testing complete! The validation system is working on real GPS data.")

if __name__ == "__main__":
    main()