import os
import openai
import json
import uuid
from datetime import date
from pydantic import ValidationError
from caltrack.models import Command

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def call_llm(user_input: str) -> Command:
    """
    Call the OpenAI API using function (tool) calling to parse the user input
    directly into a structured Command object.
    """

    system_prompt = (
        "You are CalTrack's command parser.\n"
        "Your task: Convert user natural language into a valid JSON object matching the Command schema.\n"
        "Rules:\n"
        "1. Only return a JSON object, no extra prose or explanations.\n"
        "2. Always emit 'explicit_time': true if the user mentioned a date/time.\n"
        "3. Resolve fuzzy date expressions (e.g., 'yesterday', 'next Thursday', 'Thursday before last', 'Wednesday after next') to exact ISO dates (YYYY-MM-DD), using today {today}.\n"
        "4. When intent is a specific day (e.g., 'yesterday', 'today'), encode as a single-date range (start == end).\n"
        "5. Support multi-day ranges even if composed of fuzzy start and/or end (e.g., 'from Thursday before last to Wednesday after next').\n"
        "6. For add actions, decompose multiple items into separate entries.\n"
        "7. For add actions, estimate missing numeric fields if not given.\n"
        "8. For add_weight, read_weight, etc., follow the Command schema rules.\n"
        "9. Never add commentary, apologies, or non-JSON text.\n"
        "10. Always include required 'id' and type-specific fields to match Command schema validation.\n"
        "11. For activities, interpret 'consumed' as synonymous with 'burned', and always encode calorie values as negative.\n"
        "12. For delete actions, support deletion by entry ID, by specific date, or by date range. Always confirm with the user before deleting date-based data.\n"
        "13. If the user says 'show [type]' or 'show all [type]', interpret as a read action for all records of that type. Do not include 'target.date' or 'range' unless explicitly stated.\n"
    ).format(today=date.today().isoformat())

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "parse_command",
                    "description": "Parse natural language into a structured Command object.",
                    "parameters": Command.model_json_schema()
                }
            }
        ],
        tool_choice={"type": "function", "function": {"name": "parse_command"}}
    )

    choice = response['choices'][0]
    message = choice['message']
    if 'tool_calls' not in message or not message['tool_calls']:
        raise ValueError('LLM did not return a tool_call.')

    tool_call = message['tool_calls'][0]
    if 'function' not in tool_call or 'arguments' not in tool_call['function']:
        raise ValueError('Tool call missing function or arguments.')

    args_str = tool_call['function']['arguments']
    print("DEBUG raw args:", args_str)

    try:
        args = json.loads(args_str)

        # Populate missing IDs and defaults
        if 'entries' in args:
            for entry in args['entries']:
                entry.setdefault('id', uuid.uuid4().hex[:8])
                if 'kcal_burned' in entry and entry['kcal_burned'] is None:
                    entry['kcal_burned'] = 0
                if 'volume_ml' in entry and entry['volume_ml'] is None:
                    entry['volume_ml'] = 0
                if 'kg' in entry and entry['kg'] is None:
                    entry['kg'] = 0

        if 'target' in args and args['target'] is not None:
            args['target'].setdefault('id', uuid.uuid4().hex[:8])
            args['target'].setdefault('contains', '')
    
            # Sanity fallback: ensure date is None if missing
            args['target'].setdefault('date', None)

        # Defensive check: if read/delete with no date or range, ensure type is provided
        action = args.get("action")
        target = args.get("target")
        if action in {"read", "delete"} and target:
            if not target.get("date") and not args.get("range") and not target.get("type"):
                raise ValueError("Ambiguous command: missing 'target.date', 'range', or 'type'.")

        return Command(**args)

    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"Failed to parse Command from LLM: {str(e)}")
