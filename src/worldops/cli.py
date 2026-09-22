"""Run fixture generation and placement evaluation locally."""

import argparse
import json
from pathlib import Path

from .engine import plan
from .fixture import make_factory


def main() -> None:
    parser = argparse.ArgumentParser(description="WorldOps synthetic infrastructure planner")
    parser.add_argument("world", nargs="?", type=Path, help="Input world JSON; omitted for 200-node fixture")
    parser.add_argument("--output", type=Path, help="Write comparison receipt JSON")
    parser.add_argument("--nodes-per-rack", type=int, default=10)
    parser.add_argument("--racks", type=int, default=20)
    args = parser.parse_args()
    world = json.loads(args.world.read_text()) if args.world else make_factory(args.racks, args.nodes_per_rack)
    result = {
        "world_label": world.get("fixture_kind", "user_supplied_unverified"),
        "node_count": len(world["nodes"]),
        "comparisons": {name: plan(world, name) for name in ("first_fit", "cheapest", "worldops")},
    }
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized)
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
