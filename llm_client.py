#!/usr/bin/env python3
import os
import json
import openai
from caltrack.models import Command

# Load API key at import-time
_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEFAULT_OPEN_AI_KEY")
if not _api_key:
    raise RuntimeError(
        "Set OPENAI_API_KEY (or DEFAULT_OPEN_AI_KEY) in your shell before running caltrack"
    )
openai.api_key = _api_key

# You’ll fill in the full JSON schema here

SYSTEM_PROMPT = """
You are a function‑calling assistant for a calorie/activity/fluid tracker.
Return *only* JSON matching this Command schema.

SCHEMA:
{schema}

RULES:
1. Always emit "explicit_time" (boolean): true iff user mentioned a date/time.
2. For tracker add (action=="add"):
   • entries[] must be array of objects with *only*:
     – type: "food" | "activity" | "fluid"
     – date: ISO date string or resolved relative date
     – meal: (food only) one of breakfast|brunch|lunch|afternoon snack|dinner|late snack|late night snack
       • If user gives a clock‑time instead of meal, convert it to the correct meal category.
     – description: string
     – kcal (food), kcal_burned (activity), or volume_ml (fluid)
   • Do *not* emit "id" or "ts".
   • If no date mentioned or if relative phrase used, set "needs_confirmation": true.
3. Decompose multiple items into separate entries.
4. Always estimate missing numeric fields if user omits them.
5. Include rules for add_weight, read_weight, etc.
6. Allow config actions for setting weight_kg, sex, etc.
7. NEVER output prose—JSON only.
"""


def call_llm(sentence: str) -> Command | str:
    # Fill in the actual schema JSON from caltrack.models.Command
    schema = Command.model_json_schema()    
    schema_json = json.dumps(schema, indent=2)
    prompt = SYSTEM_PROMPT.replace("{schema}", schema_json)
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system",  "content": prompt},
            {"role": "user",    "content": sentence},
        ],
    )
    content = resp.choices[0].message.content
    try:
        return Command.model_validate_json(content)
    except Exception:
        # If the model asks for clarification or mis‑formats, return raw string
        return content
