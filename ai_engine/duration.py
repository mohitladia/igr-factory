from __future__ import annotations

import math


class DurationValidationError(ValueError):
    """Raised when a generated runtime exceeds its target tolerance."""


def validate_runtime_duration(
    actual_seconds: float,
    target_seconds: int | float,
    tolerance_seconds: int | float = 15,
) -> None:
    """Reject narration timelines that materially exceed the requested target.

    The target is a generation goal, not a time-stretch instruction. A modest
    tolerance accommodates natural speech timing and the visual tail added to
    each beat. This is intentionally strict enough to stop runaway generation
    before a poor-quality video is rendered.
    """
    values = (actual_seconds, target_seconds, tolerance_seconds)
    if any(not math.isfinite(float(value)) for value in values):
        raise DurationValidationError("Duration values must be finite numbers")
    actual = float(actual_seconds)
    target = float(target_seconds)
    tolerance = float(tolerance_seconds)

    if actual <= 0:
        raise DurationValidationError("Actual runtime must be greater than zero")
    if target <= 0:
        raise DurationValidationError("Target duration must be greater than zero")
    if tolerance < 0:
        raise DurationValidationError("Duration tolerance cannot be negative")

    maximum_seconds = target + tolerance
    if actual > maximum_seconds:
        over_by = actual - target
        raise DurationValidationError(
            f"Generated runtime is {actual:.1f}s, which exceeds the {target:.1f}s target by {over_by:.1f}s "
            f"(allowed tolerance: {tolerance:.1f}s; maximum: {maximum_seconds:.1f}s). "
            "Shorten the narration, choose a longer --duration, or increase the configured duration tolerance."
        )
