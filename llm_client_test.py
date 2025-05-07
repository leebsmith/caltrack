import json
import os

from caltrack.llm_client import call_llm

def test_llm_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable is not set or empty.")
        print("TIP: Did you run 'source ~/.bashrc' or restart your terminal to load updated env vars?")
        return

    print(f"DEBUG: Retrieved OPENAI_API_KEY starts with: {api_key[:5]}... (truncated)")

    test_prompts = [
        "I had scrambled eggs for breakfast",
        "I rode an e-bike for 30 minutes and burned 300 calories",
        "I drank 2 liters of water",
        "I weigh 70.5 kg today",
        "Show my foods for yesterday",
        "Log lunch from Thursday before last",
        "Show all activity from Wednesday after next",
        "Display meals from Monday before last to Friday before last"
    ]

    for prompt in test_prompts:
        print(f"\nTEST PROMPT: {prompt}")
        try:
            result = call_llm(prompt)
            print(f"Parsed Command object:")

            json_str = json.dumps(result.model_dump(), indent=2, default=str)
            print(f"As JSON:\n{json_str}")

        except Exception as e:
            print(f"General error: {e}")

if __name__ == "__main__":
    test_llm_client()
