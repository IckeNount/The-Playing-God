from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from playing_god.core.counterfactual import (
    ScheduledIntervention,
    compare_counterfactual,
)
from playing_god.core.intervention import INTERVENTION_KINDS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare same-seed baseline and intervention trajectories."
        )
    )
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--days", type=int, required=True)
    parser.add_argument("--population", type=int, default=10)
    parser.add_argument("--day", type=int, default=0)
    parser.add_argument(
        "--kind",
        choices=sorted(INTERVENTION_KINDS),
        required=True,
    )
    parser.add_argument("--target", required=True)
    parser.add_argument("--theme", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--strength", type=float, default=0.70)
    parser.add_argument("--location")
    parser.add_argument("--duration", type=int, default=7)
    return parser


def _event_text(event) -> str:
    if event is None:
        return "<no event>"
    return (
        f"day {event.day} {event.kind}: "
        f"{event.description}"
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        comparison = compare_counterfactual(
            seed=args.seed,
            days=args.days,
            population=args.population,
            schedule=(
                ScheduledIntervention(
                    day=args.day,
                    kind=args.kind,
                    target_id=args.target,
                    theme=args.theme,
                    suggested_action=args.action,
                    strength=args.strength,
                    location=args.location,
                    duration=args.duration,
                ),
            ),
        )
    except ValueError as exc:
        parser.error(str(exc))

    print(
        "COUNTERFACTUAL COMPARISON | "
        f"seed={comparison.seed} | days={comparison.days}"
    )
    print(
        "Intervention: "
        f"day {args.day} {args.kind} -> {args.target} "
        f"({args.action})"
    )
    print(
        "Trajectory divergence: "
        f"{'yes' if comparison.diverged else 'no'}"
    )
    print(
        "First divergence day: "
        f"{comparison.first_divergence_day}"
    )
    print(
        "Affected agents: "
        f"{len(comparison.agent_differences)}"
    )

    for difference in comparison.agent_differences:
        print()
        print(
            f"{difference.agent_id}: "
            f"{', '.join(difference.changed_fields)}"
        )
        event_difference = difference.first_event_difference
        if event_difference is not None:
            print(
                "  baseline: "
                f"{_event_text(event_difference.baseline)}"
            )
            print(
                "  intervention: "
                f"{_event_text(event_difference.intervention)}"
            )

    print()
    print(
        "Interpretation: this is deterministic model divergence, "
        "not proof of supernatural causation."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
