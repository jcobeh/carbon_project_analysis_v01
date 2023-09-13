import os
from dotenv import load_dotenv
import logging

load_dotenv()
open_ai_key: str = os.environ.get("OPEN_AI_KEY")

