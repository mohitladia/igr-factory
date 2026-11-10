from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_render_plan(plan: dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    # The renderer only needs public-relative paths. Never serialize local filesystem paths.
    safe_plan = dict(plan)
    safe_beats = []
    for beat in plan["beats"]:
        item = {k: v for k, v in beat.items() if not k.endswith("_local")}
        safe_beats.append(item)
    safe_plan["beats"] = safe_beats
    destination.write_text(json.dumps(safe_plan, ensure_ascii=False, indent=2), encoding="utf-8")
