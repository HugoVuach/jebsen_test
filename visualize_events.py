import json
import os
from collections import defaultdict
from pathlib import Path


folder = Path("data/structured_events")
files = sorted(folder.glob("*.json"))
events_path = files[-1]

# Colors
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
RESET = "\033[0m"

def color_for_impact(impact: str) -> str:
    impact = impact.lower()
    if "élevé" in impact:
        return RED
    if "moyen" in impact:
        return YELLOW
    return GREY

# Eeading & grouping
with open(events_path, encoding="utf-8") as f:
    events = json.load(f)

by_type = defaultdict(list)
for e in events:
    by_type[e["event_type"]].append(e)

# Display
print(f"\nVisualization of events ({events_path}):\n")

for event_type, group in by_type.items():
    print(f"=== {event_type} ({len(group)}) ===")
    for e in group:
        color = color_for_impact(e["impact"])
        line = f"- [{e['impact']}] {e['country_region']} | {e['tweet_text']}"
        print(color + line + RESET)
    print()
