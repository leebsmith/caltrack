#!/usr/bin/env python3
"""
caltrack CLI entry point
Handles natural‑language commands for weight and tracker modules.
"""
import sys
import uuid
from datetime import datetime, date
from dateutil import parser as dateparser

from caltrack.llm_client import call_llm
from caltrack.domains import weight as weight_domain
from caltrack.domains import tracker as tracker_domain
from caltrack.storage.journal import append_record

# ---------------- Helper functions -----------------

def parse_date_range(range_obj):
    rtype = range_obj.type
    val = range_obj.value
    # Treat both 'absolute' and 'date' as date spans
    if rtype in ("absolute", "date"):
        # detect various separators
        if '…' in val:
            parts = [p.strip() for p in val.split('…')]
        elif '..' in val:
            parts = [p.strip() for p in val.split('..')]
        elif ' to ' in val:
            parts = [p.strip() for p in val.split(' to ')]
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


def print_weight_table(rows):
    if not rows:
        print("No weight records found.")
        return
    print(f"{'Date':<12} {'Weight(kg)':>10}  ID")
    for r in rows:
        d = dateparser.parse(r.get('ts', r.get('date'))).date().isoformat()
        print(f"{d:<12} {r['kg']:>10.2f}  {r['id']}")


def resolve_weight_target(target_obj, rows):
    if target_obj.id:
        return target_obj.id
    if target_obj.date:
        target_date = dateparser.parse(target_obj.date).date().isoformat()
        matches = [r for r in rows if dateparser.parse(r['ts']).date().isoformat() == target_date]
    elif target_obj.contains:
        matches = [r for r in rows if target_obj.contains.lower() in r.get('description','').lower()]
    else:
        matches = rows
    if not matches:
        raise ValueError("No matching weight records found")
    if len(matches) == 1:
        return matches[0]['id']
    print("Multiple matching records:")
    for idx, r in enumerate(matches, 1):
        d = dateparser.parse(r['ts']).date().isoformat()
        print(f"{idx}: {d} {r['kg']}kg id={r['id']}")
    sel = int(input("Select #: ")) - 1
    return matches[sel]['id']


def confirm_date(dstr):
    resp = input(f"Date resolved to {dstr}. Is that correct? (y/N) ")
    if resp.strip().lower().startswith('y'):
        return date.fromisoformat(dstr)
    sys.exit("Aborted by user.")

# ---------------- Main -----------------

def main():
    if len(sys.argv) < 2:
        print('Usage: caltrack "<command>"')
        sys.exit(1)
    cmd = call_llm(sys.argv[1])
    if isinstance(cmd, str):
        print(cmd)
        return

                        # --- Determine action ---
    # Priority 1: tracker ADD if entries of food/activity/fluid are present
    if getattr(cmd, 'entries', None):
        first = cmd.entries[0]
        typ0 = first.get('type') if isinstance(first, dict) else first.type
        if typ0 in ('food', 'activity', 'fluid'):
            cmd.action = 'add'
            # skip to CRUD routing
        else:
            act = cmd.action.lower().replace(' ', '_')
            # Weight-specific reads
            if act in ('show_weight', 'read_weight', 'list_weight'):
                cmd.action = 'read_weight'
            # Tracker-specific reads
            elif act in (
                'show_meals','list_meals','show_entries','list_entries',
                'show_food','list_food','show_foods','list_foods',
                'show_activity','list_activity','show_activities',
                'show_fluid','list_fluid','show_fluids','list_fluids'
            ):
                cmd.action = 'read'
            # General read/list defaults to tracker
            elif act in ('show', 'read', 'list'):
                cmd.action = 'read'
            # Add weight
            elif act in ('add_weight',):
                cmd.action = 'add_weight'
            # Weight update
            elif act in ('update_weight', 'change_weight'):
                cmd.action = 'update_weight'
            # Tracker update
            elif act in ('update', 'change', 'modify'):
                cmd.action = 'update'
            # Weight delete
            elif act in ('delete_weight', 'remove_weight'):
                cmd.action = 'delete_weight'
            # Tracker delete by default
            elif act in ('delete', 'remove'):
                cmd.action = 'delete'
    else:
        # No entries => follow standard mapping
        act = cmd.action.lower().replace(' ', '_')
        if act in ('show_weight', 'read_weight', 'list_weight'):
            cmd.action = 'read_weight'
        elif act in ('add_weight',):
            cmd.action = 'add_weight'
        elif act in ('update_weight', 'change_weight'):
            cmd.action = 'update_weight'
        elif act in ('delete_weight', 'remove_weight'):
            cmd.action = 'delete_weight'
        elif act in ('delete', 'remove'):
            cmd.action = 'delete'
        elif act in ('update', 'change', 'modify'):
            cmd.action = 'update'
        elif act in ('show', 'read', 'list',
                     'show_meals','list_meals','show_entries','list_entries',
                     'show_food','list_food','show_foods','list_foods',
                     'show_activity','list_activity','show_activities',
                     'show_fluid','list_fluid','show_fluids','list_fluids'):
            # defaults to read/logical grouping
            # if it mentions meals/food etc, 'read', else if generic, default to 'read'
            cmd.action = 'read'

    # ---------------- Weight CRUD ----------------
    # Add weight
    if cmd.action == 'add_weight' and getattr(cmd, 'entries', None):
        for e in cmd.entries:
            ts = datetime.fromisoformat(e.ts) if cmd.explicit_time else datetime.now().astimezone()
            rec = weight_domain.add(ts, e.kg)
            print(f"✔ weight added: {rec['kg']} kg @ {rec['ts']}")
        return

    # Read weight
    if cmd.action == 'read_weight':
        if getattr(cmd, 'range', None):
            start, end = parse_date_range(cmd.range)
            rows = weight_domain.list_weights(start, end)
        else:
            rows = weight_domain.list_weights()
        fmt = getattr(cmd, 'format', None)
        if fmt and fmt.lower().startswith('ma'):
            window = int(''.join(filter(str.isdigit, fmt.lower()))) if any(c.isdigit() for c in fmt) else 3
            ma = weight_domain.daily_moving_average(rows, window)
            print(f"Date        {window}-day MA (kg)")
            for d, val in sorted(ma.items()):
                print(f"{d.isoformat():<12} {val:>6.2f}")
        elif fmt and fmt.lower() == 'daily':
            da = weight_domain.daily_averages(rows)
            print(f"Date        Daily Avg (kg)")
            for d, val in sorted(da.items()):
                print(f"{d.isoformat():<12} {val:>6.2f}")
        else:
            print_weight_table(rows)
        return

    # Update weight
    if cmd.action == 'update_weight':
        if getattr(cmd, 'entries', None) and cmd.entries[0].kg is not None:
            e = cmd.entries[0]
            updated = weight_domain.update(e.id, e.kg)
            print(f"✔ weight updated: {updated['kg']} kg @ {updated['ts']}")
            return
        if cmd.target and getattr(cmd, 'set', None) and 'kg' in cmd.set:
            updated = weight_domain.update(cmd.target.id, cmd.set['kg'])
            print(f"✔ weight updated: {updated['kg']} kg @ {updated['ts']}")
            return
        print("Error: missing weight value or target for update.")
        return

    # Delete weight
    if cmd.action == 'delete_weight' and getattr(cmd.target, 'id', None):
        rows = weight_domain.list_weights()
        wid = resolve_weight_target(cmd.target, rows)
        weight_domain.delete(wid)
        print(f"✔ weight entry {wid} deleted")
        return

    # ---------------- Tracker ADD ----------------
    if cmd.action == 'add' and getattr(cmd, 'entries', None):
        for e in cmd.entries:
            # determine date: explicit vs default (today)
            if cmd.explicit_time:
                # use the date/time provided by LLM
                date_str = e.get('date') if isinstance(e, dict) else e.date
                if cmd.needs_confirmation:
                    d = confirm_date(date_str)
                else:
                    d = date.fromisoformat(date_str)
            else:
                # default to today and always confirm
                today_str = date.today().isoformat()
                d = confirm_date(today_str)

            # generate ID
            eid = uuid.uuid4().hex[:8]
            # extract common fields
            typ = e.get('type') if isinstance(e, dict) else e.type
            desc = e.get('description') if isinstance(e, dict) else e.description

            # build and persist record by type
            if typ == 'food':
                meal = e.get('meal') if isinstance(e, dict) else e.meal
                kcal = e.get('kcal') if isinstance(e, dict) else e.kcal
                rec = tracker_domain.add_food(eid, d, meal, desc, kcal)
            elif typ == 'activity':
                kcal_b = e.get('kcal_burned') if isinstance(e, dict) else e.kcal_burned
                rec = tracker_domain.add_activity(eid, d, desc, kcal_b)
            elif typ == 'fluid':
                vol = e.get('volume_ml') if isinstance(e, dict) else e.volume_ml
                rec = tracker_domain.add_fluid(eid, d, desc, vol)
            else:
                print('Unknown type'); continue
            append_record(rec)
            print(f"✔ logged {rec}")
        return

            # ---------------- Tracker READ ----------------
    if cmd.action == 'read':
        # Determine date window: explicit range or target.date or open
        if getattr(cmd, 'range', None):
            start, end = parse_date_range(cmd.range)
        elif getattr(cmd.target, 'date', None):
            date_str = cmd.target.date
            # multi-day if contains separator
            if ' to ' in date_str or '…' in date_str or '..' in date_str:
                # parse as absolute span
                class TempR: pass
                tmp = TempR()
                tmp.type = 'absolute'
                tmp.value = date_str
                start, end = parse_date_range(tmp)
            else:
                dt = dateparser.parse(date_str).date()
                start = end = dt
        else:
            start = end = None
        # Fetch entries in range
        rows = tracker_domain.list_entries(start, end)
        if not rows:
            print('No tracker entries found.')
            return
        # Print a simple table
        print(f"{'Date':<12} {'Type':<8} {'Desc':<30} {'Val':<6} ID")
        for r in rows:
            val = r.get('kcal') or r.get('kcal_burned') or r.get('volume_ml')
            print(f"{r['date']:<12} {r['type']:<8} {r['description'][:30]:<30} {val:<6} {r['id']}")
        return
        # Print a simple table
        print(f"{'Date':<12} {'Type':<8} {'Desc':<30} {'Val':<6} ID")
        for r in rows:
            val = r.get('kcal') or r.get('kcal_burned') or r.get('volume_ml')
            print(f"{r['date']:<12} {r['type']:<8} {r['description'][:30]:<30} {val:<6} {r['id']}")
        return
        print(f"{'Date':<12} {'Type':<8} {'Desc':<30} {'Val':<6} ID")
        for r in rows:
            val = r.get('kcal') or r.get('kcal_burned') or r.get('volume_ml')
            print(f"{r['date']:<12} {r['type']:<8} {r['description'][:30]:<30} {val:<6} {r['id']}")
        return

    # ---------------- Tracker UPDATE ----------------
    if cmd.action == 'update':
        if getattr(cmd, 'entries', None) and cmd.entries[0].id:
            e = cmd.entries[0]
            changes = {k: v for k, v in e.dict().items() if v is not None and k not in ('id','date','type')}
            updated = tracker_domain.update_entry(e.id, changes)
            print(f"✔ tracker record updated: {updated}")
            return
        if cmd.target and getattr(cmd,'set',None):
            updated = tracker_domain.update_entry(cmd.target.id, cmd.set)
            print(f"✔ tracker record updated: {updated}")
            return
        print('Error: missing target or changes for update.'); return

    # ---------------- Tracker DELETE ----------------
    if cmd.action == 'delete' and getattr(cmd.target,'id', None):
        try:
            tracker_domain.delete_entry(cmd.target.id)
            print(f"✔ tracker record {cmd.target.id} deleted")
        except KeyError as ex:
            print(str(ex))
        return

    # Fallback
    print('Unrecognized or unhandled action:', cmd.action)

if __name__ == '__main__':
    main()
