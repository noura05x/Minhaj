"""Configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Model configurations
RESEARCHER_MODEL = "llama-3.1-8b-instant"
SYNTHESIZER_MODEL = "llama-3.1-8b-instant"
STRUCTURE_MODEL = "llama-3.3-70b-versatile"
VALIDATOR_MODEL = "llama-3.1-8b-instant"
CONTENT_MODEL = "llama-3.3-70b-versatile"



# Search configuration
MAX_SEARCH_RESULTS = 5
SEARCH_DEPTH = "advanced"


# Output directories


OUTPUT_BASE_DIR = "course"


def get_output_paths(week_num, day_num):
    """
    Generate output paths for a specific day
    
    Args:
        week_num: Week number (1-based)
        day_num: Day number (1-based, global across all weeks)
    
    Returns:
        Dictionary with paths for week_dir, day_dir, slides, lab, quiz
    """
    week_dir = os.path.join(OUTPUT_BASE_DIR, f"week_{week_num:02d}")
    day_dir = os.path.join(week_dir, f"day_{day_num:02d}")
    
    return {
        "week_dir": week_dir,
        "day_dir": day_dir,
        "slides": os.path.join(day_dir, f"slides_{day_num}.qmd"),
        "lab": os.path.join(day_dir, f"lab_{day_num}.qmd"),
        "quiz": os.path.join(day_dir, f"quiz_{day_num}.qmd")
    }


MAX_SEARCH_RESULTS = 5
SEARCH_DEPTH = "advanced"