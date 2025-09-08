# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a DSPy-based triathlon race strategy optimization system that uses AI to generate personalized race strategies for athletes. The system analyzes course profiles, athlete capabilities, and race conditions to produce detailed pacing plans and strategic recommendations.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env to add your API keys (OPENAI_API_KEY or ANTHROPIC_API_KEY)
```

### Running the Application
```bash
# Run the basic demo
python examples/basic_demo.py

# For development/testing individual components
python -m src.pipelines.core_strategy  # If you add a main block
```

### Code Quality
```bash
# Format and lint with Ruff (replaces Black + flake8)
ruff format src/ tests/ examples/       # Format code
ruff check src/ tests/ examples/        # Lint code
ruff check --fix src/ tests/ examples/  # Auto-fix issues

# Or run both together
ruff format . && ruff check --fix .

# Run tests
pytest tests/

# Run specific test file
pytest tests/unit/test_models.py -v

# Run with coverage
pytest --cov=src tests/
```

## Architecture Overview

### DSPy Pipeline Architecture
The system uses DSPy's declarative programming model to chain multiple AI reasoning steps:

1. **Signatures** (`src/pipelines/signatures.py`): Define input/output contracts for each reasoning step
   - `CourseAnalyzer`: Analyzes race course characteristics
   - `AthleteAssessment`: Evaluates athlete capabilities vs course demands
   - `PacingStrategy`: Generates discipline-specific pacing plans
   - `RiskAssessment`: Identifies and mitigates race risks
   - `StrategyOptimizer`: Synthesizes final strategy with predictions

2. **Pipeline** (`src/pipelines/core_strategy.py`): 
   - `RaceStrategyPipeline` orchestrates the multi-step reasoning process
   - Each step uses `dspy.ChainOfThought` for explainable reasoning
   - Data flows through formatters that convert structured models to prompts

### Data Models (`src/models/`)
- **`course.py`**: `CourseProfile` and `ClimbSegment` for race course data
- **`athlete.py`**: `AthleteProfile` with fitness metrics and experience
- **`conditions.py`**: `RaceConditions` for environmental factors

### Configuration (`src/utils/config.py`)
- Uses DSPy 3.x API with `dspy.LM` class
- Supports multiple LLM providers (OpenAI, Anthropic, Together)
- Provider selection via `DEFAULT_LM_PROVIDER` environment variable
- Model selection via provider-specific environment variables
- Models are specified with provider prefix (e.g., "openai/gpt-3.5-turbo")

## Key Implementation Details

### DSPy Integration Pattern
- Each reasoning step is a `dspy.Signature` subclass defining the reasoning task
- The pipeline uses `dspy.ChainOfThought` to wrap signatures for better reasoning
- Data formatting methods convert Python dataclasses to structured text prompts
- Results chain together, with each step's output feeding into the next

### Adding New Features
1. Define new signatures in `src/pipelines/signatures.py` for reasoning steps
2. Add data models in `src/models/` if needed
3. Integrate into `RaceStrategyPipeline.generate_strategy()` method
4. Update formatters to handle new data structures

### Testing Strategy
- Unit tests for models and data validation
- Integration tests for full pipeline execution
- Mock LLM responses for deterministic testing
- Use fixtures for sample course/athlete data

## Environment Variables

Required in `.env`:
- `DEFAULT_LM_PROVIDER`: "openai", "anthropic", or "together"
- `OPENAI_API_KEY`: If using OpenAI (set as environment variable)
- `ANTHROPIC_API_KEY`: If using Anthropic
- `OPENAI_MODEL`: Optional, defaults to "gpt-3.5-turbo" (avoid non-existent models like "gpt-5")
- `ANTHROPIC_MODEL`: Optional, defaults to "claude-3-sonnet-20240229"

Note: DSPy 3.x uses the format "provider/model" internally (e.g., "openai/gpt-3.5-turbo")