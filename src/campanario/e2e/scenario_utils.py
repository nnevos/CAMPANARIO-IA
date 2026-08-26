from __future__ import annotations

import random

from .types import CheckSpec


def c(kind: str, value: object | None = None, *, severity: str = "fail", label: str = "") -> CheckSpec:
    return CheckSpec(kind=kind, value=value, severity=severity, label=label)


def choose(rng: random.Random, values: tuple):
    return values[rng.randrange(len(values))]
