# caltrack/summary.py
from collections import defaultdict
from datetime import datetime, timedelta

def summarize_entries(entries, start_date, end_date, verbose=False):
    daily_summary = defaultdict(lambda: {
        'food': 0,
        'activity': 0,
        'fluids_ml': 0,
        'meals': defaultdict(lambda: {'kcal': 0, 'details': []}),
        'activities': [],
        'fluid_groups': defaultdict(list)
    })

    for e in entries:
        e_date = datetime.fromisoformat(e['date']).date()
        if start_date <= e_date <= end_date:
            if e['type'] == 'food' and e.get('kcal') is not None:
                meal = e.get('meal', 'unspecified')
                daily_summary[e_date]['food'] += e['kcal']
                daily_summary[e_date]['meals'][meal]['kcal'] += e['kcal']
                if verbose:
                    daily_summary[e_date]['meals'][meal]['details'].append(e)
            elif e['type'] == 'activity' and e.get('kcal_burned') is not None:
                daily_summary[e_date]['activity'] += e['kcal_burned']
                if verbose:
                    daily_summary[e_date]['activities'].append(e)
            elif e['type'] == 'fluid' and e.get('volume_ml') is not None:
                daily_summary[e_date]['fluids_ml'] += e['volume_ml']
                fluid_group = e.get('description', 'unspecified')
                daily_summary[e_date]['fluid_groups'][fluid_group].append(e)

    total_food = sum(day['food'] for day in daily_summary.values())
    total_activity = sum(day['activity'] for day in daily_summary.values())
    total_fluids = sum(day['fluids_ml'] for day in daily_summary.values())
    net = total_food - total_activity
    days_count = (end_date - start_date).days + 1
    avg_net = net / days_count if days_count else 0

    print(f"Summary {start_date} to {end_date}:")
    print(f"  Total intake (food): {total_food} kcal")
    print(f"  Total burned (activity): {total_activity} kcal")
    print(f"  Total fluids: {total_fluids} ml")
    print(f"  Net: {net:+} kcal")
    print(f"  Daily average net: {avg_net:.1f} kcal/day")

    for day in sorted((start_date + timedelta(days=i)) for i in range(days_count)):
        day_data = daily_summary[day]
        food = day_data['food']
        activity = day_data['activity']
        fluids = day_data['fluids_ml']
        net = food - activity
        print(f"\n{day}:")

        if food > 0:
            print(f"  Intake: {food} kcal")
            for meal, data in day_data['meals'].items():
                print(f"    {meal.capitalize()}: {data['kcal']} kcal")
                if verbose and data['details']:
                    for e in data['details']:
                        desc = e.get('description', 'unknown')
                        eid = e.get('id', 'unknown')
                        val = f"{e.get('kcal', '?')} kcal"
                        print(f"      - [food] {desc} (id={eid}): {val}")
        else:
            print(f"  Intake: 0 kcal")

        if activity > 0:
            print(f"  Burned: {activity} kcal")
            if verbose and day_data['activities']:
                for e in day_data['activities']:
                    desc = e.get('description', 'unknown')
                    eid = e.get('id', 'unknown')
                    val = f"{e.get('kcal_burned', '?')} kcal burned"
                    print(f"    - [activity] {desc} (id={eid}): {val}")
        else:
            print(f"  Burned: 0 kcal")

        if fluids > 0:
            print(f"  Fluids: {fluids} ml")
            if verbose and day_data['fluid_groups']:
                for fluid_desc, fluid_list in day_data['fluid_groups'].items():
                    group_total = sum(e.get('volume_ml', 0) for e in fluid_list)
                    print(f"    {fluid_desc}: {group_total} ml")
                    for e in fluid_list:
                        eid = e.get('id', 'unknown')
                        val = f"{e.get('volume_ml', '?')} ml"
                        print(f"      - [fluid] (id={eid}): {val}")
        else:
            print(f"  Fluids: 0 ml")

        print(f"  Net: {net:+} kcal")
