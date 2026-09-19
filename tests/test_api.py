from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_subject_not_found():
    response = client.get("/api/v1/subjects/nonexistent")
    assert response.status_code == 404

def test_get_subject_exists():
    # '042-S01-001' is a known subject
    response = client.get("/api/v1/subjects/042-S01-001")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "evidence" in data
    assert data["data"]["USUBJID"] == "042-S01-001"
    
    evidence = data["evidence"]["records"]
    assert len(evidence) == 1
    assert evidence[0]["file"] == "DM.csv"
    assert evidence[0]["row_id"]["USUBJID"] == "042-S01-001"
