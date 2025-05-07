import json
from caltrack.storage.journal import read_all_records

def main():
    records = read_all_records()
    if not records:
        print("No records found in ~/.caltrack/entries.ndjson")
        return

    food_count = sum(1 for r in records if r.get('type') == 'food')
    activity_count = sum(1 for r in records if r.get('type') == 'activity')
    fluid_count = sum(1 for r in records if r.get('type') == 'fluid')
    weight_count = sum(1 for r in records if r.get('type') == 'weight')

    print(f"Found {len(records)} total records:")
    print(f"  Foods: {food_count}")
    print(f"  Activities: {activity_count}")
    print(f"  Fluids: {fluid_count}")
    print(f"  Weights: {weight_count}")

    for r in records:
        print(json.dumps(r, indent=2))

if __name__ == "__main__":
    main()
