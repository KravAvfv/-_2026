"""REST API для периферійних шлюзів."""
from datetime import timedelta

from conftest import one

H = {"X-Gateway-Token": "demo-gateway-token"}


def test_detection_api(client, conn):
    s = one(conn, "SELECT hw_serial FROM sensor WHERE status = 'у мережі' AND kind = 'радіолокаційний' LIMIT 1")
    t = (one(conn, "SELECT now()") - timedelta(seconds=1)).isoformat()
    body = {"sensor": s, "detected_at": t, "lat": 51.8, "lon": 31.1, "alt": 180, "speed": 50, "confidence": 0.9}
    r = client.post("/api/v1/detections", json=body, headers=H)
    assert r.status_code == 201 and r.get_json()["track_number"].startswith("ЩП-")
    assert client.post("/api/v1/detections", json=body, headers={"X-Gateway-Token": "x"}).status_code == 401
    off = one(conn, "SELECT hw_serial FROM sensor WHERE status = 'поза мережею' LIMIT 1")
    assert client.post("/api/v1/detections", json={**body, "sensor": off}, headers=H).status_code == 422
    assert client.post("/api/v1/detections", json={"sensor": s}, headers=H).status_code == 422


def test_threats_api(client):
    assert client.get("/api/v1/threats").status_code == 401
    th = client.get("/api/v1/threats", headers=H).get_json()["threats"]
    scores = [t["threat_score"] for t in th]
    assert scores and scores == sorted(scores, reverse=True)
