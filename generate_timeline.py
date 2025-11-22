import json
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt



STRUCTURED_DIR = Path("data/structured_events")
OUTPUT_PNG = Path("timeline_events.png")


def load_latest_events(path: Path):
    """Load the most recent *_events.json file from the given directory."""
    files = sorted(path.glob("*.json"))
    latest = files[-1]
    with latest.open(encoding="utf-8") as f:
        return json.load(f)


def parse_datetime(dt_str: str) -> datetime:
    # Replace trailing 'Z' with '+00:00' so fromisoformat accepts it
    if dt_str.endswith("Z"):
        dt_str = dt_str.replace("Z", "+00:00")
    return datetime.fromisoformat(dt_str)


def color_for_impact(impact: str) -> str:
    """Return a matplotlib color based on impact."""
    impact = impact.lower()
    if "élevé" in impact or "eleve" in impact:
        return "red"
    if "moyen" in impact:
        return "gold"
    return "grey"


def main():
    events = load_latest_events(STRUCTURED_DIR)

    event_types = sorted({e["event_type"] for e in events})
    type_to_y = {etype: i for i, etype in enumerate(event_types)}

    xs = []
    ys = []
    colors = []

    for e in events:
        dt = parse_datetime(e["tweet_created_at"])
        etype = e["event_type"]
        impact = e["impact"]

        xs.append(dt)
        ys.append(type_to_y.get(etype, -1))
        colors.append(color_for_impact(impact))

    plt.figure(figsize=(12, 4))
    plt.scatter(xs, ys, c=colors, s=60)

    plt.yticks(
        ticks=list(type_to_y.values()),
        labels=list(type_to_y.keys()),
    )

    plt.xlabel("Time")
    plt.ylabel("Event type")
    plt.title("Financial events timeline by impact")

    plt.grid(axis="x", linestyle="--", alpha=0.4)
    plt.tight_layout()

    plt.savefig(OUTPUT_PNG, dpi=150)
    plt.close()

    print(f"Timeline saved to: {OUTPUT_PNG}")


if __name__ == "__main__":
    main()
