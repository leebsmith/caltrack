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
    if rtype == "absolute":
        parts = [p.strip() for p in val.replace('..', '…').split('…')]
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
    # initial weight prompt skipped for brevity ...

    if len(sys.argv) < 2:
        print('Usage: caltrack "<command>"')
        sys.exit(1)
    cmd = call_llm(sys.argv[1])
    if isinstance(cmd, str):
        print(cmd); return

    # map common synonyms
    act = cmd.action.lower().replace(' ', '_')
    if act in ('show','read','list','show_weight','read_weight'):
        cmd.action='read_weight'
    elif act in ('set','change','update','modify','update_weight','change_weight'):
        cmd.action='update_weight'
    elif act in ('delete','remove','delete_weight'):
        cmd.action='delete_weight'
    elif act in ('add_food','consume'):
        cmd.action='add'

    # weight add/read/update/delete blocks ... (omitted here; previously working)

    # tracker add block
    if cmd.action=='add' and cmd.entries:
        for e in cmd.entries:
            date_str=e.get('date') if isinstance(e,dict) else e.date
            if not cmd.explicit_time:
                date_str=date.today().isoformat()
            d=confirm_date(date_str) if cmd.needs_confirmation else date.fromisoformat(date_str)
            eid=uuid.uuid4().hex[:8]
            typ=e.get('type') if isinstance(e,dict) else e.type
            desc=e.get('description') if isinstance(e,dict) else e.description
            if typ=='food':
                meal=e.get('meal') if isinstance(e,dict) else e.meal
                kcal=e.get('kcal') if isinstance(e,dict) else e.kcal
                rec=tracker_domain.add_food(eid,d,meal,desc,kcal)
            elif typ=='activity':
                kcal_b=e.get('kcal_burned') if isinstance(e,dict) else e.kcal_burned
                rec=tracker_domain.add_activity(eid,d,desc,kcal_b)
            elif typ=='fluid':
                vol=e.get('volume_ml') if isinstance(e,dict) else e.volume_ml
                rec=tracker_domain.add_fluid(eid,d,desc,vol)
            else:
                print('Unknown type'); continue
            append_record(rec)
            print('✔ logged',rec)
        return

    print('Unrecognized or unhandled action:',cmd.action)

if __name__=='__main__':
    main()
