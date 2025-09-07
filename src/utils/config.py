import os
from dotenv import load_dotenv
import dspy

load_dotenv()

def setup_dspy_model():
    """Configure DSPy with the appropriate language model"""
    provider = os.getenv("DEFAULT_LM_PROVIDER", "openai").lower()
    
    if provider == "openai":
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        lm = dspy.OpenAI(model=model, max_tokens=1000)
    elif provider == "anthropic":
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        lm = dspy.Claude(model=model)
    elif provider == "together":
        lm = dspy.Together(model="mistralai/Mistral-7B-Instruct-v0.1")
    else:
        raise ValueError(f"Unsupported LM provider: {provider}")
    
    dspy.settings.configure(lm=lm)
    return lm
