import uuid
from datetime import date, datetime
from pathlib import Path
from caltrack.domains import tracker as tracker_domain
from caltrack.domains import weight as weight_domain

if __name__ == "__main__":
    print("Running full diagnostic test (food, fluid, activity, weight)...")

    today = date.today()

    # Add food entry
    food_id = uuid.uuid4().hex[:8]
    tracker_domain.add_food(food_id, today, "test_meal", "diagnostic food item", 123)
    print(f"✔ Added food entry (id={food_id})")

    # Add fluid entry
    fluid_id = uuid.uuid4().hex[:8]
    tracker_domain.add_fluid(fluid_id, today, "diagnostic fluid item", 500)
    print(f"✔ Added fluid entry (id={fluid_id})")

    # Add activity entry
    activity_id = uuid.uuid4().hex[:8]
    tracker_domain.add_activity(activity_id, today, "diagnostic activity item", 200)
    print(f"✔ Added activity entry (id={activity_id})")

    # Add weight entry (ensure 'type' field included to satisfy journal)
    weight_id = uuid.uuid4().hex[:8]
    weight_rec = {
        "id": weight_id,
        "type": "weight",
        "ts": datetime.now().isoformat(),
        "kg": 70.5
    }
    from caltrack.storage.journal import append_record
    append_record(weight_rec)
    print(f"✔ Added weight entry (id={weight_id})")

    # List all tracker entries
    print("\nCurrent tracker entries:")
    tracker_entries = tracker_domain.list_entries()
    for e in tracker_entries:
        print(f"  {e}")

    # List all weight entries
    print("\nCurrent weight entries:")
    weight_entries = weight_domain.list_weights()
    for e in weight_entries:
        print(f"  {e}")

    # Print raw file contents (shared file)
    print("\nRaw file contents (~/.caltrack/entries.ndjson):")
    journal_path = Path.home() / ".caltrack" / "entries.ndjson"
    if journal_path.exists():
        with open(journal_path, "r") as f:
            for line in f:
                print(line.strip())
    else:
        print("No entries.ndjson file found.")
