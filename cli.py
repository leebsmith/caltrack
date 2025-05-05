import sys
import uuid
from datetime import datetime, date
from dateutil import parser as dateparser
from caltrack.llm_client import call_llm
from caltrack.models import Command, WeightEntry, FoodEntry, ActivityEntry, FluidEntry
from caltrack.domains import weight as weight_domain
from caltrack.domains import tracker as tracker_domain
from caltrack.summary import summarize_entries

def parse_date_range(range_obj):
    rtype = range_obj.type
    val = range_obj.value
    if rtype in ("absolute", "date"):
        parts = [p.strip() for p in val.replace('…', '..').replace(' to ', '..').replace('/', '..').split('..')]
        start = end = date.fromisoformat(parts[0]) if len(parts) == 1 else (date.fromisoformat(parts[0]), date.fromisoformat(parts[1]))
    elif rtype == "relative":
        dt = dateparser.parse(val, default=datetime.now()).date()
        start = end = dt
    else:
        raise ValueError(f"Unknown range type: {rtype}")
    return start, end

def confirm_date(dstr):
    resp = input(f"Date resolved to {dstr}. Is that correct? (y/N) ").strip().lower()
    if resp.startswith('y'):
        return date.fromisoformat(dstr)
    override = input("Please enter the correct date (YYYY-MM-DD): ").strip()
    try:
        return date.fromisoformat(override)
    except ValueError:
        sys.exit("Invalid date format. Aborting.")

def handle_bulk_delete(cmd, verbose=False):
    if not cmd.target or not cmd.target.date or not cmd.target.type:
        print("Bulk delete requires both a target date and type (food, activity, fluid, weight).")
        return

    target_type = cmd.target.type.lower()
    date_str = cmd.target.date
    dt = dateparser.parse(date_str, default=datetime.now()).date()

    if target_type == 'weight':
        entries = weight_domain.list_weights()
        matching = [r for r in entries if datetime.fromisoformat(r['ts']).date() == dt]
    else:
        entries = tracker_domain.list_entries()
        matching = [r for r in entries if r.get('type') == target_type and datetime.fromisoformat(r['date']).date() == dt]

    if not matching:
        print(f"No matching {target_type} entries found for {dt}.")
        return

    print(f"Found {len(matching)} {target_type} entries on {dt}:")
    for r in matching:
        print(f"  ID {r['id']}: {r['description']}")

    confirm = input("Delete all these entries? (y/N) ").strip().lower()
    if not confirm.startswith('y'):
        print("Aborted.")
        return

    deleted_count = 0
    for r in matching:
        try:
            if target_type == 'weight':
                weight_domain.delete(r['id'])
            else:
                tracker_domain.delete_entry(r['id'])
            deleted_count += 1
            if verbose:
                print(f"✔ Deleted {r['id']} ({r['description']})")
        except Exception as ex:
            print(f"Failed to delete {r['id']}: {str(ex)}")

    print(f"✔ Deleted {deleted_count} {target_type} entries for {dt}.")

def main():
    verbose = '--verbose' in sys.argv
    command_input = ' '.join(arg for arg in sys.argv[1:] if arg != '--verbose')

    if not command_input:
        print('Usage: caltrack "<command>" [--verbose]')
        sys.exit(1)

    cmd = call_llm(command_input)
    if isinstance(cmd, str):
        print(cmd)
        return

    act = cmd.action.lower().replace(' ', '_')

    requested_type = None
    if 'food' in act:
        requested_type = 'food'
    elif 'activity' in act:
        requested_type = 'activity'
    elif 'fluid' in act:
        requested_type = 'fluid'
    elif 'weight' in act:
        requested_type = 'weight'

    if requested_type == 'weight':
        rows = weight_domain.list_weights()
        if not rows:
            print('No weight records found.')
            return
        print(f"{'Date':<12} {'Weight(kg)':>10}  ID")
        for r in rows:
            d = datetime.fromisoformat(r['ts']).date().isoformat()
            print(f"{d:<12} {r['kg']:>10.2f}  {r['id']}")
        return

    if act in ('show', 'read', 'list', 'show_meals', 'list_meals', 'show_food', 'list_foods', 'show_activity', 'list_activity', 'show_activities', 'show_fluid', 'list_fluid', 'show_fluids', 'show_all'):
        cmd.action = 'read'
    elif act in ('add', 'add_food', 'consume'):
        cmd.action = 'add'
    elif act == 'add_weight':
        cmd.action = 'add_weight'
    elif act in ('update', 'change', 'modify'):
        cmd.action = 'update'
    elif act in ('update_weight', 'change_weight'):
        cmd.action = 'update_weight'
    elif act in ('delete', 'remove'):
        cmd.action = 'delete'
    elif act in ('delete_weight', 'remove_weight'):
        cmd.action = 'delete_weight'

    if cmd.action == 'read':
        tracker_rows = tracker_domain.list_entries()
        combined_rows = tracker_rows

        if requested_type:
            combined_rows = [r for r in combined_rows if r.get('type') == requested_type]

        if not combined_rows:
            print('No entries found.')
            return

        if cmd.range:
            start, end = parse_date_range(cmd.range)
        elif cmd.target and cmd.target.date:
            date_str = cmd.target.date
            if any(sep in date_str for sep in (' to ', '…', '..', '/')):
                class Tmp: pass
                tmp = Tmp(); tmp.type = 'absolute'; tmp.value = date_str
                start, end = parse_date_range(tmp)
            else:
                dt = dateparser.parse(date_str, default=datetime.now()).date()
                start = end = dt
        else:
            all_dates = [datetime.fromisoformat(r['date']).date() for r in combined_rows if r.get('date')]
            if all_dates:
                start, end = min(all_dates), max(all_dates)
            else:
                print('No dated entries found.')
                return

        summarize_entries(combined_rows, start, end, verbose=verbose)
        return

    if cmd.action == 'add_weight' and cmd.entries:
        for e in cmd.entries:
            ts = datetime.fromisoformat(e.date.isoformat()) if cmd.explicit_time else datetime.now().astimezone()
            rec = weight_domain.add(ts, e.kg)
            print(f"✔ weight added: {rec['kg']} kg @ {rec['ts']} (id={rec['id']})")
        return

    if cmd.action == 'update_weight' and cmd.entries:
        e = cmd.entries[0]
        updated = weight_domain.update(e.id, e.kg)
        print(f"✔ weight updated: {updated['kg']} kg @ {updated['ts']} (id={updated['id']})")
        return

    if cmd.action == 'delete' and cmd.target and cmd.target.date and cmd.target.type:
        handle_bulk_delete(cmd, verbose=verbose)
        return

    if cmd.action == 'delete' and cmd.target and cmd.target.id:
        try:
            tracker_domain.delete_entry(cmd.target.id)
            print(f"✔ tracker record {cmd.target.id} deleted")
        except KeyError as ex:
            print(str(ex))
        return

    if cmd.action == 'delete_weight' and cmd.target and cmd.target.id:
        try:
            weight_domain.delete(cmd.target.id)
            print(f"✔ weight entry {cmd.target.id} deleted")
        except KeyError as ex:
            print(str(ex))
        return

    if cmd.action == 'add' and cmd.entries:
        for e in cmd.entries:
            date_str = e.date.isoformat()
            d = confirm_date(date_str) if cmd.needs_confirmation else date.fromisoformat(date_str)
            eid = uuid.uuid4().hex[:8]
            if isinstance(e, FoodEntry):
                tracker_domain.add_food(eid, d, e.meal, e.description, e.kcal)
            elif isinstance(e, ActivityEntry):
                tracker_domain.add_activity(eid, d, e.description, e.kcal_burned)
            elif isinstance(e, FluidEntry):
                tracker_domain.add_fluid(eid, d, e.description, e.volume_ml)
            else:
                print('Unknown type'); continue
            if verbose:
                print(f"✔ logged {e.description} on {d} (id={eid})")
            else:
                print(f"✔ logged {e.description} (id={eid})")
        return

    print('Unrecognized or unhandled action:', cmd.action)

if __name__ == '__main__':
    main()
