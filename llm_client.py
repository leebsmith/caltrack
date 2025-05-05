# llm_client.py (patched to force single date for both relative and absolute single-day phrases)
#!/usr/bin/env python3
import os
import json
import openai
from datetime import datetime, date
from dateutil import parser as dateparser
from caltrack.models import Command

# Load API key at import-time
_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEFAULT_OPEN_AI_KEY")
if not _api_key:
    raise RuntimeError(
        "Set OPENAI_API_KEY (or DEFAULT_OPEN_AI_KEY) in your shell before running caltrack"
    )
openai.api_key = _api_key

# System prompt with current date injection
SYSTEM_PROMPT = f"""
You are a function‑calling assistant for a calorie/activity/fluid tracker.
Return *only* JSON matching this Command schema.

SCHEMA:
{{schema}}

RULES:
1. Always emit "explicit_time" (boolean): true iff user mentioned a date/time.
2. When user gives fuzzy, human-readable date expressions, convert them into exact calendar dates
   – Use today's date as the anchor point for all calculations.
   – Current date (today): {date.today().isoformat()}
   – Parse fuzzy phrases such as:
         - "next Thursday"
         - "the Monday after next"
         - "two weeks from today"
         - "this past Friday"
         - "three weeks from this coming Sunday"
         - "yesterday"
   – Always return resolved date as ISO string (YYYY-MM-DD).
   – **Important:** When the intent is a specific day (e.g., "yesterday", "today", "last Friday"), always encode as a single-date range where start == end.
   – Only use multi-day ranges when the user explicitly requests a span (e.g., "from Monday to Wednesday").
3. For tracker add (action=="add"):
   • entries[] must be array of objects with *only*:
     – type: "food" | "activity" | "fluid"
     – date: resolved ISO date (absolute date, no relative phrasing)
     – meal: (food only) one of breakfast|brunch|lunch|afternoon snack|dinner|late snack|late night snack
       • If user gives a clock‑time instead of meal, convert it to the correct meal category.
     – description: string
     – kcal (food), kcal_burned (activity), or volume_ml (fluid)
   • Do *not* emit "id" or "ts".
   • If no date mentioned or if relative phrase used, set "needs_confirmation": true.
4. Decompose multiple items into separate entries.
5. Always estimate missing numeric fields if user omits them.
6. Include rules for add_weight, read_weight, etc.
7. Allow config actions for setting weight_kg, sex, etc.
8. NEVER output prose—JSON only.

Current date: {date.today().isoformat()}
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
        result = Command.model_validate_json(content)

        # POSTPROCESSING FIX: force range start == end if intent was single-day
        if result.range:
            if result.range.type == "relative" or (result.range.type == "absolute" and (' to ' not in result.range.value and '…' not in result.range.value and '..' not in result.range.value and '/' not in result.range.value)):
                parsed_date = dateparser.parse(result.range.value, default=datetime.now()).date()
                result.range.start = parsed_date.isoformat()
                result.range.end = parsed_date.isoformat()

        return result
    except Exception:
        # If the model asks for clarification or mis‑formats, return raw string
        return content
