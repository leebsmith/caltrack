import sys
import uuid
import json
from datetime import datetime, date
from dateutil import parser as dateparser
from caltrack.llm_client import call_llm
from caltrack.domains import weight as weight_domain
from caltrack.domains import tracker as tracker_domain
from caltrack.summary import summarize_entries

def parse_date_range(cmd_data):
    if 'range' in cmd_data and cmd_data['range'] and cmd_data['range'].get('value'):
        val = cmd_data['range']['value']
        try:
            if any(sep in val for sep in ('..', '…', ' to ', '/')):
                parts = [p.strip() for p in val.replace('…', '..').replace(' to ', '..').replace('/', '..').split('..')]
                start = date.fromisoformat(parts[0])
                end = date.fromisoformat(parts[1])
            else:
                start = end = date.fromisoformat(val)
        except ValueError:
            parsed = dateparser.parse(val, default=datetime.now()).date()
            start = end = parsed
        return start, end
    return None, None

def confirm_date(dstr):
    resp = input(f"Date resolved to {dstr}. Is that correct? (y/N) ").strip().lower()
    if resp.startswith('y'):
        return date.fromisoformat(dstr)
    override = input("Please enter the correct date (YYYY-MM-DD): ").strip()
    try:
        return date.fromisoformat(override)
    except ValueError:
        sys.exit("Invalid date format. Aborting.")

def main():
    verbose = '--verbose' in sys.argv
    command_input = ' '.join(arg for arg in sys.argv[1:] if arg != '--verbose')

    if not command_input:
        print('Usage: caltrack "<command>" [--verbose]')
        sys.exit(1)

    structured_cmd = None
    try:
        structured_cmd = call_llm(command_input)
    except Exception as e:
        print(f"ERROR: {e}")
        return

    print("DEBUG: Structured LLM response:", structured_cmd)

    if not structured_cmd or not structured_cmd.action:
        print("ERROR: LLM returned no action.")
        return

    action = structured_cmd.action.lower().replace(' ', '_')

    if action == 'delete':
        if structured_cmd.target and structured_cmd.target.id:
            eid = structured_cmd.target.id
            deleted = tracker_domain.delete_entry(eid)
            if not deleted:
                deleted = weight_domain.delete(eid)
            if deleted:
                print(f"✔ deleted entry with id={eid}")
            else:
                print(f"✘ no entry found with id={eid}")
            return
        start, end = parse_date_range(structured_cmd.model_dump())
        if not start or not end:
            print("ERROR: No valid date or range found for deletion.")
            return
        confirm = input(f"WARNING: This will delete all entries from {start} to {end}. Proceed? (y/N) ").strip().lower()
        if confirm != 'y':
            print("Aborted by user.")
            return
        entries = tracker_domain.list_entries()
        to_delete = [e for e in entries if start <= datetime.fromisoformat(e['date']).date() <= end]
        for e in to_delete:
            tracker_domain.delete_entry(e['id'])
        print(f"✔ deleted {len(to_delete)} entries from {start} to {end}")
        return

    if action in ('add', 'add_food', 'consume') and structured_cmd.entries:
        for e in structured_cmd.entries:
            date_str = e.date.isoformat()
            d = confirm_date(date_str) if structured_cmd.needs_confirmation else date.fromisoformat(date_str)
            eid = uuid.uuid4().hex[:8]

            if hasattr(e, 'meal') and hasattr(e, 'kcal'):
                rec = tracker_domain.add_food(eid, d, e.meal, e.description, e.kcal)
                print(f"✔ logged food: {rec['description']} (id={rec['id']})")
            elif hasattr(e, 'kcal_burned'):
                rec = tracker_domain.add_activity(eid, d, e.description, e.kcal_burned)
                print(f"✔ logged activity: {rec['description']} (id={rec['id']})")
            elif hasattr(e, 'volume_ml'):
                rec = tracker_domain.add_fluid(eid, d, e.description, e.volume_ml)
                print(f"✔ logged fluid: {rec['description']} (id={rec['id']})")
            elif hasattr(e, 'kg'):
                ts = datetime.combine(d, datetime.min.time())
                rec = weight_domain.add(ts, e.kg)
                print(f"✔ weight added: {rec['kg']} kg @ {rec['ts']} (id={rec['id']})")
            else:
                print(f"Unknown entry type, skipping: {e}")
        return

    if action in ('show', 'read', 'list', 'show_all'):
        entries = tracker_domain.list_entries()
        if not entries:
            print('No entries found.')
            return

        requested_type = structured_cmd.target.type if structured_cmd.target and structured_cmd.target.type else 'all'
        if requested_type != 'all':
            entries = [e for e in entries if e.get('type') == requested_type]

        start, end = parse_date_range(structured_cmd.dict())
        if not start or not end:
            all_dates = [datetime.fromisoformat(e['date']).date() for e in entries if e.get('date')]
            if all_dates:
                start = min(all_dates)
                end = max(all_dates)
                print(f"DEBUG: Defaulting to full range: {start} to {end}")
            else:
                print("DEBUG: No dates found in entries")
                return

        summarize_entries(entries, start, end, verbose=verbose)
        return

    if action in ('show_weight', 'read_weight', 'list_weight'):
        weights = weight_domain.list_weights()
        if not weights:
            print('No weight records found.')
            return
        print(f"{'Date':<12} {'Weight(kg)':>10}  ID")
        for w in weights:
            d = datetime.fromisoformat(w['ts']).date().isoformat()
            print(f"{d:<12} {w['kg']:>10.2f}  {w['id']}")
        return

    print(f"Unrecognized or unsupported action: {action}")

if __name__ == '__main__':
    main()
