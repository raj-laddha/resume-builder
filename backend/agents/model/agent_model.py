import os
from dotenv import load_dotenv
from agno.models.google import Gemini
from agno.models.lmstudio import LMStudio

# Load environment variables
load_dotenv()

MODEL_PROVIDER = os.getenv("AGENTS_MODEL_PROVIDER", "Gemini")
MODEL_ID = os.getenv("AGENTS_MODEL_ID")

model_config = {
    "Gemini": {
        "get_model": lambda: Gemini(id=(MODEL_ID or "gemini-2.0-flash"))
    },
    "LMStudio": {
        "get_model": lambda: LMStudio(id=MODEL_ID)
    }
}

def load_model():
    try:
        model = model_config[MODEL_PROVIDER]["get_model"]()
        
        return model
        
    except KeyError:
        raise ValueError(f"Unsupported MODEL_PROVIDER: {MODEL_PROVIDER}")
    

agent_model = load_model()