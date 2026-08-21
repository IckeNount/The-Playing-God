from __future__ import annotations

import json
import random
from typing import Any


def create_rng(seed: int) -> random.Random:
    """
    Create the exact same dedicated RNG style used by Phase 1.
    """
    return random.Random(seed)


def serialize_state(rng: random.Random) -> str:
    """
    Convert Random.getstate() into JSON text suitable for SQLite.
    """
    return json.dumps(rng.getstate())


def _lists_to_tuples(value: Any) -> Any:
    """
    JSON converts tuples to lists.
    random.Random.setstate() expects tuples again.
    """
    if isinstance(value, list):
        return tuple(_lists_to_tuples(item) for item in value)

    return value


def restore_state(
    rng: random.Random,
    serialized_state: str,
) -> None:
    """
    Restore the RNG to the exact saved position in its random stream.
    """
    raw_state = json.loads(serialized_state)
    state = _lists_to_tuples(raw_state)
    rng.setstate(state)