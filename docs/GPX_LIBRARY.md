# GPX Course Library

The race strategy optimizer now supports a library of GPX files for accurate course analysis. This document explains how to use and manage the GPX course library.

## Overview

The GPX library system allows you to:
- Store GPX files in the `data/` directory
- Automatically process them into course JSON files
- Load courses using convenient functions
- Compare different versions of the same course

## Directory Structure

```
data/                           # GPX file library
├── alpedhuez_triathlon.gpx    # Alpe d'Huez triathlon course
└── im70.3_pennstate.gpx       # Happy Valley 70.3 GPS data

src/data/courses/               # Generated course JSON files
├── alpedhuez_triathlon.json
├── happy_valley_70_3_real.json
└── im70.3_pennstate.json

scripts/
└── process_gpx_library.py      # Process all GPX files
```

## Processing GPX Files

### Automatic Processing

Run the GPX library processor to convert all GPX files:

```bash
python scripts/process_gpx_library.py
```

This will:
1. Scan the `data/` directory for `.gpx` files
2. Parse each GPX file using the GPS parser
3. Generate course JSON files in `src/data/courses/`
4. Apply course-specific metadata and formatting

### Example Output

```
🚴‍♂️ GPX Library Processor
========================================
📂 Data directory: /path/to/data
💾 Output directory: /path/to/src/data/courses

📋 Found 2 GPX file(s):
   - im70.3_pennstate.gpx
   - alpedhuez_triathlon.gpx

🔍 Processing: im70.3_pennstate.gpx
   📊 Course: Ironman 70.3 Happy Valley (GPS)
   🚴 Distance: 56.1 miles
   ⛰️  Elevation: 5,062 ft
   🧗 Key Climbs: 8
✅ Course JSON saved to: .../im70.3_pennstate.json

🎉 Successfully processed 2 course(s)!
```

## Loading Courses

### Using Predefined Loaders

```python
from src.utils.course_loader import (
    load_happy_valley_70_3,      # Research-based profile
    load_happy_valley_70_3_gps,  # GPS-based profile  
    load_alpe_dhuez              # Alpe d'Huez triathlon
)

# Load courses
research_course = load_happy_valley_70_3()
gps_course = load_happy_valley_70_3_gps()
alpine_course = load_alpe_dhuez()
```

### Using Generic Loader

```python
from src.utils.course_loader import load_course, get_available_courses

# See all available courses
courses = get_available_courses()
print(courses)  # ['alpedhuez_triathlon', 'happy_valley_70_3_real', 'im70.3_pennstate']

# Load any course by name
course = load_course('alpedhuez_triathlon')
```

## Available Courses

### Happy Valley 70.3 - Research-Based
- **Loader**: `load_happy_valley_70_3()`
- **File**: `happy_valley_70_3_real.json`
- **Elevation**: 3,487 ft
- **Source**: Research-based realistic profile
- **Key Features**: 5 major climb segments, well-defined technical sections

### Happy Valley 70.3 - GPS-Based  
- **Loader**: `load_happy_valley_70_3_gps()`
- **File**: `im70.3_pennstate.json`
- **Elevation**: 5,062 ft
- **Source**: Actual GPS track data
- **Key Features**: 8 climb segments, 35 technical sections, more detailed elevation profile

### Alpe d'Huez Triathlon L
- **Loader**: `load_alpe_dhuez()`
- **File**: `alpedhuez_triathlon.json`  
- **Elevation**: 15,715 ft
- **Source**: GPS track data
- **Key Features**: 17 major climbs, extreme mountain profile, famous 21 switchbacks

## Course Comparison

The system allows comparing different versions of courses:

```python
research_course = load_happy_valley_70_3()     # 3,487 ft elevation
gps_course = load_happy_valley_70_3_gps()     # 5,062 ft elevation

# GPS shows +1,575 ft more elevation than research estimate
# GPS detected 3 additional significant climb segments
```

## Adding New Courses

### Step 1: Add GPX File
1. Place your `.gpx` file in the `data/` directory
2. Use descriptive filenames (e.g., `ironman_coeur_dalene.gpx`)

### Step 2: Configure Course Metadata
Edit `scripts/process_gpx_library.py` and add course-specific information:

```python
course_configs = {
    "your_course.gpx": {
        "name": "Your Course Name",
        "location": "Location, Country",
        "altitude_ft": 1000,
        "swim_venue": "Lake/Ocean Name",
        "bike_profile": "Rolling/Hilly/Mountain",
        "run_profile": "Flat/Rolling/Hilly",
        # ... other metadata
    }
}
```

### Step 3: Process the Library
```bash
python scripts/process_gpx_library.py
```

### Step 4: Add Convenience Loader (Optional)
Add a loader function to `src/utils/course_loader.py`:

```python
def load_your_course() -> CourseProfile:
    """Load Your Course Name"""
    return load_course_from_json("your_course")
```

## Data Quality

### GPS Data Quality Metrics
- **Data Quality Score**: Percentage based on missing elevation points
- **Total GPS Points**: Number of track points in the GPX file
- **Missing Elevation**: Count of points without elevation data
- **Bounds**: Geographic bounding box of the course

### Course Validation
The processor automatically validates:
- ✅ GPX file format and structure
- ✅ Minimum required track points
- ✅ Elevation data availability
- ✅ Distance calculations
- ✅ Climb detection accuracy

## Technical Details

### Supported GPX Features
- Multiple tracks and track segments
- Elevation data (required for climb detection)
- Geographic coordinates (latitude/longitude)
- Timestamps (optional, used for metadata)

### Climb Detection Parameters
- **Minimum climb grade**: 3% (configurable)
- **Minimum climb distance**: 0.5 miles (configurable)
- **Smoothing window**: 5 points (configurable)
- **Descent detection**: -8% threshold (configurable)

### Course JSON Format
```json
{
  "name": "Course Name",
  "location": "Location",
  "bike_distance_miles": 56.1,
  "bike_elevation_gain_ft": 5062,
  "key_climbs": [
    {
      "name": "Climb Name",
      "start_mile": 38.3,
      "length_miles": 2.1,
      "avg_grade": 10.9,
      "max_grade": 23.8,
      "elevation_gain_ft": 374
    }
  ],
  "technical_sections": ["Description of technical areas"],
  "data_source": {
    "type": "GPS Track",
    "source": "Local GPX file",
    "data_quality_score": 98.5,
    "total_gps_points": 2847
  }
}
```

## Best Practices

### GPX File Quality
- Use high-resolution GPS tracks (≥1 point per 10 meters)
- Ensure elevation data is present
- Prefer bike computer exports over phone apps
- Clean up any data spikes or errors before processing

### File Naming
- Use descriptive names: `ironman_wisconsin_bike.gpx`
- Include race type if relevant: `70.3_steelhead.gpx`
- Avoid spaces and special characters
- Use lowercase with underscores

### Course Metadata
- Research official course descriptions
- Include geographic and elevation context
- Specify technical difficulty level
- Note any course changes between years