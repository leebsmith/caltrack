#!/usr/bin/env python3
"""
caltrack CLI entry point
Handles natural‑language commands for weight and tracker modules.
"""
import sys
import uuid
from datetime import datetime, date

from caltrack.storage.journal import append_record
from caltrack.llm_client import call_llm
from caltrack.models import Command
from caltrack.domains import weight as weight_domain
from caltrack.domains import tracker as tracker_domain
from caltrack.storage.journal import append_record

def confirm_date(resolved: str) -> date:
    """Ask the user to confirm a resolved ISO date string."""
    ans = input(f"Date resolved to {resolved}. Is that correct? (y/N) ")
    if ans.strip().lower().startswith("y"):
        return date.fromisoformat(resolved)
    else:
        sys.exit("Aborted: date not confirmed.")

def main():

    # 0) First‑run weight prompt
    from caltrack.domains.weight import list_weights, add as add_weight
    from dateutil import parser as dateparser

    weights = list_weights()
    if not weights:
        # no weight on file yet
        ans = input("No weight on record. Please enter your current weight (e.g. 172 lb): ")
        # rudimentary parsing: assume '<number> lb' or '<number> kg'
        parts = ans.strip().lower().split()
        if len(parts) == 2 and parts[1] in ("lb","lbs"):
            kg = float(parts[0]) * 0.453592
        else:
            kg = float(parts[0])
        # record it now
        rec = add_weight(datetime.now(), kg)
        print(f"✔ baseline weight set to {rec['kg']:.1f} kg @ {rec['ts']}")

    if len(sys.argv) < 2:
        print('Usage: caltrack "<natural language command>"')
        sys.exit(1)

    sentence = sys.argv[1]
    cmd = call_llm(sentence)
    if isinstance(cmd, str):
        # LLM returned a clarification prompt or error message
        print(cmd)
        return

    # -- Weight commands ------------------------------------------------
    if cmd.action == 'add_weight' and cmd.entries:
        for e in cmd.entries:
            ts = datetime.fromisoformat(e.ts) if cmd.explicit_time else datetime.now().astimezone()
            rec = weight_domain.add(ts, e.kg)
            print(f"✔ weight added: {rec['kg']} kg @ {rec['ts']}")
        return

    if cmd.action == 'read_weight' and cmd.range:
        # implementation omitted for brevity
        print("✔ read_weight not yet implemented")
        return

    if cmd.action == 'update_weight' and cmd.entries:
        e = cmd.entries[0]
        updated = weight_domain.update(e.id, e.kg)
        print(f"✔ weight updated: {updated['kg']} kg @ {updated['ts']}")
        return

    if cmd.action == 'delete_weight' and cmd.target:
        rows = weight_domain.list_weights()
        # simple resolve by id if provided
        wid = cmd.target.id or rows[0]['id']
        weight_domain.delete(wid)
        print(f"✔ weight entry {wid} deleted")
        return

    # -- Tracker (food/activity/fluid) commands -------------------------
    if cmd.action == 'add' and cmd.entries:
        for e in cmd.entries:
            # determine date
            if cmd.needs_confirmation:
                d = confirm_date(e.date)
            else:
                d = date.fromisoformat(e.date)
            # generate ID
            eid = uuid.uuid4().hex[:8]
            # build record
            if e.type == 'food':
                rec = tracker_domain.add_food(eid, d, e.meal, e.description, e.kcal)
            elif e.type == 'activity':
                rec = tracker_domain.add_activity(eid, d, e.description, e.kcal_burned)
            elif e.type == 'fluid':
                rec = tracker_domain.add_fluid(eid, d, e.description, e.volume_ml)
            else:
                print(f"Unknown entry type: {e.type}")
                continue
            # persist and report
            append_record(rec)
            if e.type == 'food':
                print(f"✔ food: {rec['kcal']} kcal of '{rec['description']}' on {rec['date']} ({rec['meal']})")
            elif e.type == 'activity':
                print(f"✔ activity: {rec['kcal_burned']} kcal burned '{rec['description']}' on {rec['date']}")
            else:
                print(f"✔ fluid: {rec['volume_ml']} ml '{rec['description']}' on {rec['date']}")
        return

    # Fallback for any other or unhandled action
    print(f"Unrecognized or unhandled action: {cmd.action}")

if __name__ == '__main__':
    main()
