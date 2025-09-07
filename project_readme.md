# DSPy Race Strategy Optimizer 🏊‍♂️🚴‍♂️🏃‍♂️

A comprehensive race strategy AI system built with DSPy for triathlon optimization. Generate intelligent pacing strategies, risk assessments, and performance predictions for Ironman 70.3 races.

## 🎯 What This Project Does

- **Course Analysis**: Deep dive into elevation profiles, technical sections, and strategic challenges
- **Athlete Assessment**: Match individual capabilities to course demands
- **Pacing Strategy**: Generate detailed power/pace recommendations by segment
- **Risk Management**: Identify potential race-day issues and mitigation plans
- **Performance Prediction**: Realistic time estimates with success probability

## 🏁 Supported Races

- **Ironman 70.3 Happy Valley** (Pennsylvania) - Complete course data
- **Alpe d'Huez Triathlon** (France) - The legendary 21 bends climb
- *Extensible to any triathlon course*

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/yourusername/dspy-race-strategy.git
cd dspy-race-strategy
chmod +x setup.sh && ./setup.sh
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys
```bash
cp .env.example .env
# Edit .env with your OpenAI/Anthropic API keys
```

### 4. Run Your First Strategy
```bash
python examples/basic_demo.py
```

## 🏗️ Architecture

### DSPy Pipeline Overview
```
Course Data → Course Analyzer → Athlete Assessor → Pacing Strategist → Risk Assessor → Strategy Optimizer
```

### Core Components

- **`src/models/`** - Data structures for courses, athletes, conditions
- **`src/pipelines/`** - DSPy signature definitions and pipeline logic
- **`src/data/`** - Course profiles and athlete templates
- **`src/utils/`** - Validation, formatting, and helper functions

### DSPy Signatures
- `CourseAnalyzer` - Extract strategic insights from course profiles
- `AthleteAssessment` - Match athlete capabilities to course demands
- `PacingStrategy` - Generate discipline-specific pacing plans
- `RiskAssessment` - Identify and mitigate race-day risks
- `StrategyOptimizer` - Synthesize complete race execution plan

## 📊 Example Output

```
🎯 Final Strategy:
Conservative start, build through bike segments 2-3, attack the mile 38 climb at 85% FTP, 
negative split run targeting 7:45 pace for first 6 miles...

⏱️ Time Prediction:
Swim: 32:00 | T1: 3:00 | Bike: 2:45:00 | T2: 2:00 | Run: 1:58:00 | Total: 5:20:00

📈 Success Probability: 78% chance of sub-5:30 finish
```

## 🔧 Adding New Features

### New Course
```python
# Add to src/data/courses/
YOUR_RACE_COURSE = CourseProfile(
    name="Your Race Name",
    bike_distance_miles=56.0,
    bike_elevation_gain_ft=2000,
    # ... more data
)
```

### New DSPy Module
```python
class NutritionStrategy(dspy.Signature):
    """Generate race nutrition plan"""
    athlete_profile: str = dspy.InputField()
    race_duration: str = dspy.InputField()
    
    hydration_plan: str = dspy.OutputField()
    fuel_schedule: str = dspy.OutputField()
```

## 🧪 Development with Claude Code

This project is designed for iterative development with Claude Code:

```bash
# Add new features
claude-code --message "Add a nutrition planning module that integrates with the race strategy pipeline"

# Refactor and improve
claude-code --message "Help me optimize the DSPy signatures for better performance and accuracy"

# Add real data
claude-code --message "Help me integrate GPS course data from Ride with GPS into our course models"
```

## 📈 Learning DSPy Path

### Beginner (Week 1)
- Run basic demo and understand pipeline flow
- Modify athlete profiles and see strategy changes
- Add simple course data

### Intermediate (Week 2-3)
- Create new DSPy signatures
- Implement few-shot learning examples
- Add validation and error handling

### Advanced (Week 4+)
- Optimize signatures with DSPy compilation
- Build evaluation metrics
- Create comparative analysis tools

## 🗂️ Project Structure

```
dspy-race-strategy/
├── src/
│   ├── models/           # Data structures
│   ├── pipelines/        # DSPy signatures and logic
│   ├── data/            # Course and athlete data
│   └── utils/           # Helper functions
├── tests/               # Unit and integration tests
├── examples/            # Demo scripts and tutorials
├── docs/               # Documentation
└── scripts/            # Automation and setup
```

## 🎓 Why This Project for Learning DSPy?

- **Multi-step reasoning**: See how DSPy chains complex analysis
- **Real-world application**: Solve actual triathlon strategy problems
- **Structured outputs**: Practice reliable information extraction
- **Domain integration**: Learn to incorporate specialized knowledge
- **Extensible design**: Easy to add new features as you learn

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Roadmap

- [ ] **v0.1**: Core pipeline with Happy Valley course
- [ ] **v0.2**: Alpe d'Huez integration + real GPS data
- [ ] **v0.3**: Nutrition and equipment modules
- [ ] **v0.4**: DSPy optimization and few-shot learning
- [ ] **v0.5**: Web interface and strategy comparison tools
- [ ] **v1.0**: Multi-race support with performance tracking

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **DSPy Team** - For the amazing framework
- **Triathlon Community** - For course data and domain expertise
- **Happy Valley 70.3** & **Alpe d'Huez Triathlon** - For inspiring this project

---

**Ready to optimize your race strategy with AI?** 🚀

Get started with the basic demo and join the community of athletes using AI to improve their performance!
