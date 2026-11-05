"""Transparent priority scoring. Unknown context is never silently guessed."""
from typing import Any

THRESHOLDS = [(75, "critical"), (50, "high"), (25, "medium"), (0, "low")]
WEIGHTS = {
    "pothole": {"visible_severity": 30, "road_exposure": 25, "safety_context": 20, "recurrence": 15, "duration": 10},
    "garbage_accumulation": {"visible_extent": 30, "public_obstruction": 25, "location_context": 15, "recurrence": 15, "duration": 15},
}

def level_for(score: float) -> str:
    for floor, label in THRESHOLDS:
        if score >= floor:
            return label
    return "low"

def score_issue(category: str, factors: dict[str, float | None]) -> dict[str, Any]:
    if category not in WEIGHTS:
        raise ValueError("Unsupported category")
    weights = WEIGHTS[category]
    known = {name: max(0.0, min(100.0, float(factors[name]))) for name in weights if factors.get(name) is not None}
    if not known:
        return {"score": None, "level": "unassessed", "components": [], "note": "Insufficient verified context to calculate priority."}
    known_weight = sum(weights[name] for name in known)
    components = []
    score = 0.0
    for name, value in known.items():
        effective_weight = weights[name] / known_weight
        contribution = value * effective_weight
        score += contribution
        components.append({"factor": name, "value": round(value, 2), "configured_weight": weights[name], "normalised_weight": round(effective_weight, 4), "contribution": round(contribution, 2)})
    return {"score": round(score, 2), "level": level_for(score), "components": components, "weights": weights, "note": "Score is provisional and based only on supplied factors; unknown factors were excluded and remaining weights were normalised."}

def image_area_severity(detections: list[dict], image_width: int, image_height: int, category: str) -> float | None:
    """A coarse visual proxy only; not a physical measurement of depth or mass."""
    boxes = [d["bbox_xyxy"] for d in detections if d.get("category") == category]
    if not boxes or image_width <= 0 or image_height <= 0:
        return None
    areas = []
    total_area = image_width * image_height
    for x1, y1, x2, y2 in boxes:
        areas.append(max(0, x2-x1) * max(0, y2-y1))
    ratio = min(1.0, sum(areas) / total_area)
    # Explicitly a visual extent proxy; field calibration is required.
    return round(min(100.0, ratio * 250.0), 2)
