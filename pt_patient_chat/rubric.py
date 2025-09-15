
from typing import Dict, Any, List, Tuple

RUBRIC_ITEMS = [
    ("asked_onset", 1.0, "Asked onset/timeline"),
    ("asked_mechanism", 1.0, "Clarified mechanism/context"),
    ("asked_location", 0.5, "Clarified pain location"),
    ("asked_severity", 0.5, "Quantified severity (NRS)"),
    ("asked_aggravators", 1.0, "Identified aggravating factors"),
    ("asked_easers", 1.0, "Identified easing factors"),
    ("asked_24h_pattern", 0.5, "Explored 24-hour pattern"),
    ("screened_red_flags", 2.0, "Screened red flags"),
    ("asked_work_status", 0.5, "Checked work/role demands"),
    ("asked_sdoH_transport", 0.5, "Checked transport/access"),
    ("asked_goals", 1.0, "Established patient goals"),
    ("asked_exam", 1.5, "Discussed or referenced exam findings"),
]

def score_from_tags(all_tags: List[str]) -> Dict[str, Any]:
    tagset = set(all_tags or [])
    total = 0.0
    details = []
    for key, weight, label in RUBRIC_ITEMS:
        hit = key in tagset
        pts = weight if hit else 0.0
        total += pts
        details.append({"item": key, "label": label, "hit": hit, "points": pts, "max": weight})
    max_total = sum(w for _, w, _ in RUBRIC_ITEMS)
    return {
        "score": round(total, 2),
        "max": round(max_total, 2),
        "percent": round(100.0 * total / max_total, 1),
        "details": details
    }
