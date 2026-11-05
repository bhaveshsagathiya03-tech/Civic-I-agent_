from app.services.priority import score_issue, level_for

def test_unknown_factors_are_not_guessed():
    result = score_issue("pothole", {"visible_severity": 60, "road_exposure": None, "safety_context": None, "recurrence": None, "duration": None})
    assert result["score"] == 60
    assert result["level"] == "high"
    assert len(result["components"]) == 1

def test_no_factors_means_unassessed():
    result = score_issue("garbage_accumulation", {"visible_extent": None, "public_obstruction": None, "location_context": None, "recurrence": None, "duration": None})
    assert result["score"] is None
    assert result["level"] == "unassessed"

def test_priority_bands():
    assert level_for(80) == "critical"
    assert level_for(65) == "high"
    assert level_for(30) == "medium"
    assert level_for(10) == "low"
