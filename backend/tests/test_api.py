from __future__ import annotations


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_creates_pending_assets(client):
    payload = {
        "brand": "jade",
        "topic": "gold price volatility and stock cover",
        "platforms": ["linkedin"],
        "languages": ["en"],
        "variants": 1,
        "include_video": False,
    }
    response = client.post("/api/content/generate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"]
    assert len(body["assets"]) >= 1
    assert all(a["status"] == "pending_review" for a in body["assets"])


def test_review_decision_requires_reason_for_rejection(client):
    payload = {
        "brand": "doctorshield",
        "topic": "indemnity limits for clinics",
        "platforms": ["linkedin"],
        "languages": ["en"],
        "variants": 1,
        "include_video": False,
    }
    asset = client.post("/api/content/generate", json=payload).json()["assets"][0]

    bad = client.post(
        f"/api/review/{asset['id']}/decision",
        json={"decision": "reject", "editor": "tester"},
    )
    assert bad.status_code == 422

    good = client.post(
        f"/api/review/{asset['id']}/decision",
        json={
            "decision": "reject",
            "editor": "tester",
            "reason_tag": "too_salesy",
            "note": "Reads like an ad.",
        },
    )
    assert good.status_code == 200
    assert good.json()["status"] == "rejected"


def test_approve_then_publish_flow(client):
    payload = {
        "brand": "jaguar_transit",
        "topic": "transit cover for high-value electronics",
        "platforms": ["linkedin"],
        "languages": ["en"],
        "variants": 1,
        "include_video": False,
    }
    asset = client.post("/api/content/generate", json=payload).json()["assets"][0]

    approved = client.post(
        f"/api/review/{asset['id']}/decision",
        json={"decision": "approve", "editor": "tester"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    run = client.post("/api/publishing/run")
    assert run.status_code == 200
    assert run.json()["count"] >= 1

    results = client.get("/api/publishing/results").json()
    assert any(r["asset_id"] == asset["id"] for r in results)


def test_analytics_overview(client):
    response = client.get("/api/analytics/overview")
    assert response.status_code == 200
    assert "total_assets" in response.json()