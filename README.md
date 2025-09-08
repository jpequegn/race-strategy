# Race Strategy Optimizer 🏊‍♂️🚴‍♂️🏃‍♂️

AI-powered triathlon race strategy optimization using DSPy's declarative programming framework. Generate personalized pacing plans, risk assessments, and strategic recommendations based on course profiles, athlete capabilities, and race conditions.

## Features

- **Multi-step AI reasoning** - Chain-of-thought analysis across 5 specialized modules
- **Personalized strategies** - Tailored to athlete strengths, limiters, and experience
- **Course-aware planning** - Analyzes elevation, technical sections, and key segments
- **Risk mitigation** - Identifies potential issues and provides contingency plans
- **Time predictions** - Realistic finish time estimates with discipline splits

## Quick Start

```bash
# Clone and setup
git clone https://github.com/jpequegn/race-strategy.git
cd race-strategy
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your OpenAI or Anthropic API key

# Run demo
python examples/basic_demo.py
```

## How It Works

The system uses DSPy to orchestrate a pipeline of AI reasoning steps:

1. **Course Analysis** - Identifies strategic opportunities and challenges
2. **Athlete Assessment** - Evaluates capabilities relative to course demands  
3. **Pacing Strategy** - Generates discipline-specific power/pace targets
4. **Risk Assessment** - Identifies and mitigates potential race day issues
5. **Strategy Optimization** - Synthesizes final plan with success probability

## GPS Course Analysis

The system includes comprehensive GPS parsing and analysis capabilities for real-world course data:

### Example GPX Files

Five representative courses demonstrate different racing scenarios:

- **🟢 Flat Course** - Minimal elevation (51ft gain, ~25 miles) - Perfect for time trials and beginners
- **🟡 Hilly Course** - Rolling terrain (2,800ft gain, ~35 miles) - 4 major climbs with varied gradients
- **🔴 Mountain Course** - Extreme alpine (6,200ft gain, ~28 miles) - High altitude with 15%+ grades  
- **🏙️ Urban Course** - City racing (1,200ft gain, ~22 miles) - Bridges, short climbs, technical sections
- **⚠️ Edge Cases** - Data quality testing (~8 miles) - GPS errors, missing data, boundary conditions

### Demo Scripts

```bash
# Basic GPS parsing demonstration
python examples/gps_demo.py

# Compare courses side-by-side  
python examples/compare_courses.py

# Advanced climb analysis with power/pacing
python examples/climb_analysis.py
```

### GPS Usage Examples

```python
from src.utils.gps_parser import GPSParser, GPSParserConfig
from src.models.course import CourseProfile

# Initialize GPS parser
config = GPSParserConfig(
    min_climb_length_miles=0.5,
    min_climb_grade=4.0,
    enable_smoothing=True
)
parser = GPSParser(config)

# Parse GPX file
course = parser.parse_gpx_file("examples/gpx/hilly_course.gpx")

# Access parsed data
print(f"Distance: {course.bike_distance_miles:.1f} miles")
print(f"Elevation gain: {course.bike_elevation_gain_ft:,} ft") 
print(f"Key climbs: {len(course.key_climbs)}")

# Analyze individual climbs
for climb in course.key_climbs:
    print(f"- {climb.name}: {climb.length_miles:.1f} mi, {climb.avg_grade:.1f}% grade")
```

## Project Structure

```
src/
├── models/          # Data models (Course, Athlete, Conditions, GPS)
├── pipelines/       # DSPy signatures and orchestration
├── utils/           # GPS parser, configuration, and helpers
└── data/courses/    # Pre-defined JSON course profiles

examples/
├── gpx/            # Example GPX files for testing/demos
├── gps_demo.py     # Basic GPS parsing demonstration
├── compare_courses.py  # Side-by-side course comparison
└── climb_analysis.py   # Advanced climbing analysis

tests/
└── unit/           # Unit tests including GPS parser tests
```

## Requirements

- Python 3.8+
- OpenAI API key (or Anthropic/Together AI)
- DSPy 3.0+

## License

MIT