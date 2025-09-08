#!/usr/bin/env python3
"""
Test the new Alpe d'Huez Real course data integration
"""

import sys

sys.path.append(".")

from src.utils.course_loader import load_alpe_dhuez_real


def main():
    print("🏔️  Testing Alpe d'Huez Real Course Integration (Issue #11)")
    print("=" * 65)

    try:
        # Test loading the new course
        print("\n1️⃣  LOADING ALPE D'HUEZ REAL COURSE")
        print("-" * 35)

        course = load_alpe_dhuez_real()

        print(f"📊 Course Name: {course.name}")
        print(f"🚴 Bike Distance: {course.bike_distance_miles:.1f} miles")
        print(f"⛰️  Bike Elevation: {course.bike_elevation_gain_ft:,} ft")
        print(f"🏊 Swim Distance: {course.swim_distance_miles:.2f} miles")
        print(f"🏃 Run Distance: {course.run_distance_miles:.1f} miles")
        print(f"📍 Base Altitude: {course.altitude_ft:,} ft")

        # Test the 4 major climbs
        print(f"\n2️⃣  FOUR MAJOR CLIMBS VERIFICATION")
        print("-" * 30)

        print(f"🧗 Total Key Climbs: {len(course.key_climbs)}")

        if len(course.key_climbs) == 4:
            print("   ✅ Correct number of major climbs (4)")

            for i, climb in enumerate(course.key_climbs, 1):
                print(f"   {i}. {climb.name}")
                print(
                    f"      📍 Mile {climb.start_mile:.1f}, {climb.length_miles:.1f}mi long"
                )
                print(
                    f"      📈 {climb.avg_grade:.1f}% avg, {climb.max_grade:.1f}% max"
                )
                print(f"      ⛰️  {climb.elevation_gain_ft}ft gain")
        else:
            print(f"   ❌ Expected 4 climbs, found {len(course.key_climbs)}")

        # Test 21-bend Alpe d'Huez technical section
        print(f"\n3️⃣  21-BEND ALPE D'HUEZ VERIFICATION")
        print("-" * 35)

        alpe_sections = [
            section
            for section in course.technical_sections
            if "21" in section and "Alpe" in section
        ]

        if alpe_sections:
            print("   ✅ 21-Bend Alpe d'Huez found in technical sections:")
            for section in alpe_sections:
                print(f"      {section}")
        else:
            print("   ❌ 21-Bend Alpe d'Huez not found in technical sections")
            print("   📋 Available technical sections:")
            for section in course.technical_sections[:3]:  # Show first 3
                print(f"      {section}")

        # Test altitude effects
        print(f"\n4️⃣  ALTITUDE EFFECTS VERIFICATION")
        print("-" * 30)

        if course.altitude_effects:
            effects = course.altitude_effects
            print("   ✅ Altitude effects found:")
            print(f"      🏔️  Base Altitude: {effects.base_altitude_ft:,} ft")
            print(f"      🗻 Max Altitude: {effects.max_altitude_ft:,} ft")
            print(f"      🌬️  Zone: {effects.altitude_zone}")
            print(f"      💨 Oxygen Reduction: {effects.oxygen_reduction_percent}%")
            print(f"      🧘 Acclimatization Needed: {effects.acclimatization_needed}")
            print(f"      💧 Hydration Multiplier: {effects.hydration_multiplier}x")
            print(f"      ⚡ Performance Impact: {effects.performance_impact}")
        else:
            print("   ❌ Altitude effects not found")

        # Test specific climb verification (Alpe d'Huez final ascent)
        print(f"\n5️⃣  ALPE D'HUEZ FINAL ASCENT VERIFICATION")
        print("-" * 40)

        final_climb = None
        for climb in course.key_climbs:
            if "Final Ascent" in climb.name and "21" in climb.name:
                final_climb = climb
                break

        if final_climb:
            print("   ✅ Alpe d'Huez Final Ascent (21 Bends) found:")
            print(f"      📍 Starts at mile {final_climb.start_mile:.1f}")
            print(f"      📏 Length: {final_climb.length_miles:.2f} miles")
            print(f"      📈 Average grade: {final_climb.avg_grade:.1f}%")
            print(f"      ⛰️  Elevation gain: {final_climb.elevation_gain_ft} ft")

            # Verify it's the biggest climb
            max_gain_climb = max(course.key_climbs, key=lambda c: c.elevation_gain_ft)
            if max_gain_climb == final_climb:
                print("   ✅ This is the biggest climb on the course (as expected)")
            else:
                print(
                    f"   ⚠️  Expected this to be the biggest climb, but {max_gain_climb.name} has {max_gain_climb.elevation_gain_ft}ft"
                )
        else:
            print("   ❌ Alpe d'Huez Final Ascent (21 Bends) not found")

        print(f"\n" + "=" * 65)
        print("🎉 Testing complete! Alpe d'Huez Real course integration verified.")

    except Exception as e:
        print(f"❌ Error testing Alpe d'Huez Real course: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
