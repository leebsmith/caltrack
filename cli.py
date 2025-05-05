# caltrack/cli.py (corrected to avoid using full range when single day like 'yesterday')
import sys
import uuid
import json
from datetime import datetime, date, timedelta
from dateutil import parser as dateparser

from caltrack.llm_client import call_llm
from caltrack.models import Command, WeightEntry, FoodEntry, ActivityEntry, FluidEntry
from caltrack.domains import weight as weight_domain
from caltrack.domains import tracker as tracker_domain
from caltrack.storage.journal import append_record
from caltrack.summary import summarize_entries

# ---------------- Helper functions -----------------

def parse_date_range(range_obj):
    rtype = range_obj.type
    val = range_obj.value
    if rtype in ("absolute", "date"):
        if '…' in val:
            parts = [p.strip() for p in val.split('…')]
        elif '..' in val:
            parts = [p.strip() for p in val.split('..')]
        elif ' to ' in val:
            parts = [p.strip() for p in val.split(' to ')]
        elif '/' in val:
            parts = [p.strip() for p in val.split('/')]
        else:
            parts = [val.strip()]
        if len(parts) == 1:
            start = end = date.fromisoformat(parts[0])
        else:
            start = date.fromisoformat(parts[0])
            end = date.fromisoformat(parts[1])
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

# ---------------- Main -----------------

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

    if act in (
        'show','read','list','show_meals','list_meals','show_food','list_foods',
        'show_activity','list_activity','show_activities','show_fluid','list_fluid','show_fluids', 'show_all'):
        cmd.action = 'read'
    elif act in ('show_weight','read_weight','list_weight'):
        cmd.action = 'read_weight'
    elif act in ('add','add_food','consume'):
        cmd.action = 'add'
    elif act == 'add_weight':
        cmd.action = 'add_weight'
    elif act in ('update','change','modify'):
        cmd.action = 'update'
    elif act in ('update_weight','change_weight'):
        cmd.action = 'update_weight'
    elif act in ('delete','remove'):
        cmd.action = 'delete'
    elif act in ('delete_weight','remove_weight'):
        cmd.action = 'delete_weight'

    if cmd.action == 'read':
        rows = tracker_domain.list_entries()
        if not rows:
            print('No tracker entries found.')
            return
        
        if cmd.range:
            start, end = parse_date_range(cmd.range)
        elif cmd.target and cmd.target.date:
            date_str = cmd.target.date
            if any(sep in date_str for sep in (' to ', '…', '..', '/')):
                class Tmp: pass
                tmp = Tmp(); tmp.type='absolute'; tmp.value=date_str
                start, end = parse_date_range(tmp)
            else:
                dt = dateparser.parse(date_str, default=datetime.now()).date()
                start = end = dt
        else:
            # Only fall back to full range if NO target or range is given
            all_dates = [datetime.fromisoformat(r['date']).date() for r in rows if r.get('date')]
            if all_dates:
                start, end = min(all_dates), max(all_dates)
            else:
                print('No dated entries found.')
                return

        summarize_entries(rows, start, end, verbose=verbose)
        return

    if cmd.action == 'read_weight':
        rows = weight_domain.list_weights()
        if not rows:
            print('No weight records found.')
            return
        if cmd.range:
            start, end = parse_date_range(cmd.range)
            rows = [r for r in rows if start <= dateparser.parse(r['ts']).date() <= end]
        if verbose:
            print(f"{'Date':<12} {'Weight(kg)':>10}  ID")
            for r in rows:
                d = dateparser.parse(r.get('ts', r.get('date'))).date().isoformat()
                print(f"{d:<12} {r['kg']:>10.2f}  {r['id']}")
        else:
            print(f"Total weight records: {len(rows)}")
        return

    if cmd.action == 'add' and cmd.entries:
        for e in cmd.entries:
            date_str = e.date.isoformat()
            d = confirm_date(date_str) if cmd.needs_confirmation else date.fromisoformat(date_str)
            eid = uuid.uuid4().hex[:8]
            if isinstance(e, FoodEntry):
                rec = tracker_domain.add_food(eid, d, e.meal, e.description, e.kcal)
            elif isinstance(e, ActivityEntry):
                rec = tracker_domain.add_activity(eid, d, e.description, e.kcal_burned)
            elif isinstance(e, FluidEntry):
                rec = tracker_domain.add_fluid(eid, d, e.description, e.volume_ml)
            else:
                print('Unknown type'); continue
            append_record(rec)
            if verbose:
                print(f"✔ logged {rec}")
            else:
                print(f"✔ logged {e.description} on {d} (id={eid})")
        return

    print('Unrecognized or unhandled action:', cmd.action)

if __name__ == '__main__':
    main()
