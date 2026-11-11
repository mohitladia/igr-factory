from __future__ import annotations

import math


def validate_runtime_duration(
    actual_seconds: float,
    target_seconds: int | float,
    tolerance_seconds: int | float = 15,
) -> None:
    """Reject narration timelines that materially exceed the requested target.

    The target is a generation goal, not a time-stretch instruction. A modest
    tolerance accommodates natural speech timing and the visual tail added to
    each beat; callers can tune it for their production workflow.
    """
    values = (actual_seconds, target_seconds, tolerance_seconds)
    if any(not math.isfinite(float(value)) for value in values):
        raise ValueError("Duration values must be finite numbers")
    if actual_seconds <= 0:
        raise ValueError("Actual runtime must be greater than zero")
    if target_seconds <= 0:
        raise ValueError("Target duration must be greater than zero")
    if tolerance_seconds < 0:
        raise ValueError("Duration tolerance cannot be negative")

    maximum_seconds = float(target_seconds) + float(tolerance_seconds)
    if float(actual_seconds) > maximum_seconds:
        over_by = float(actual_seconds) - float(target_seconds)
        raise ValueError(
            f"Generated runtime is {float(actual_seconds):.1f}s, which exceeds the "
            f"{float(target_seconds):.1f}s target by {over_by:.1f}s "
            f"(allowed tolerance: {float(tolerance_seconds):.1f}s; maximum: "
            f"{maximum_seconds:.1f}s). Shorten the narration, choose a longer "
            "--duration, or increase --duration-tolerance."
        )
