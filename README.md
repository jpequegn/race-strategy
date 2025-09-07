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

## Project Structure

```
src/
├── models/          # Data models (Course, Athlete, Conditions)
├── pipelines/       # DSPy signatures and orchestration
└── utils/           # Configuration and helpers
```

## Requirements

- Python 3.8+
- OpenAI API key (or Anthropic/Together AI)
- DSPy 3.0+

## License

MIT