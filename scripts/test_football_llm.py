
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. Load the Gemini API key
project_folder = Path(__file__).resolve().parent.parent
load_dotenv(project_folder / ".env")

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise SystemExit("Gemini API key is missing.")

# 2. Connect to the Gemini model
model = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    api_key=api_key,
)

# 3. Verified football evidence from our earlier database test
evidence = """
Source: Sportmonks football statistics
Player: Alex Král
Team: FC København
Player ID: 82032
Season ID: 27897
Snapshot date: 2026-11-15
Goals: 1
Assists: 2
Monitoring status: WAITING_FOR_HISTORY
"""

# 4. Ask the model to prepare a factual report
response = model.invoke([
    (
        "system",
        "You are ScoutMonitor AI, a football research assistant. "
        "Use only the provided evidence. "
        "Do not invent statistics, matches, or performance trends. "
        "If historical data is missing, explain that comparisons "
        "cannot yet be made. "
        "Write a short professional football report."
    ),
    (
        "human",
        "Prepare a short football intelligence report "
        "using this evidence:\n\n" + evidence
    ),
])

# 5. Display the AI-generated report
print("ScoutMonitor AI - Gemini Report")
print(response.text)
