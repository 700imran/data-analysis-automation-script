from pathlib import Path
from fastapi.testclient import TestClient
from marginpulse_engine.api import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_health_is_public():
    response = client.get("/health")
    assert response.status_code == 200


def test_analyze_requires_api_key():
    response = client.get("/api/v1/modules")
    assert response.status_code == 401


def test_api_upload_and_download(tmp_path, monkeypatch):
    import marginpulse_engine.api as api
    monkeypatch.setattr(api, "STORAGE_ROOT", tmp_path)
    path = ROOT / "examples" / "distributor_demo.xlsx"
    with path.open("rb") as handle:
        response = client.post(
            "/api/v1/analyze",
            headers={"X-API-Key": api.API_KEY},
            data={"config": '{"client_id":"api-test","profile":"distributor","currency":"AED","as_of_date":"2026-10-31"}'},
            files={"files": (path.name, handle, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "sales_intelligence" in [x["module"] for x in body["module_availability"] if x["available"]]
    analysis_id = body["summary"]["analysis_id"]
    download = client.get(f"/api/v1/analyses/{analysis_id}/download?client_id=api-test", headers={"X-API-Key": api.API_KEY})
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/zip"
