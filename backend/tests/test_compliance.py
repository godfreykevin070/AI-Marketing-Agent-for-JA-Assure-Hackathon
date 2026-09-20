from __future__ import annotations

from app.agents.compliance_agent import (
    deterministic_screen,
    evaluate_assets,
    summarize_verdicts,
)


def test_banned_phrase_is_caught():
    asset = {
        "title": "Guaranteed cover",
        "body": "We offer guaranteed payout on every claim.",
        "cta": "",
    }
    screen = deterministic_screen(asset)
    assert screen["deterministic_fail"] is True
    assert screen["deterministic_spans"]


def test_missing_disclaimer_is_caught():
    asset = {
        "title": "Our policy",
        "body": "Our policy covers your stock and your transit exposure in full.",
        "cta": "",
    }
    screen = deterministic_screen(asset)
    assert screen["deterministic_fail"] is True
    assert any("C6" in r for r in screen["deterministic_reasons"])


def test_clean_asset_with_disclaimer_passes_pre_screen():
    asset = {
        "title": "Reviewing your limits",
        "body": (
            "Your declared limits may have drifted from today's values. "
            "Cover is subject to policy terms and underwriting."
        ),
        "cta": "Talk to a specialist.",
    }
    screen = deterministic_screen(asset)
    assert screen["deterministic_fail"] is False


def test_evaluate_assets_returns_a_verdict_per_asset():
    assets = [
        {"title": "A", "body": "Guaranteed returns on every policy.", "cta": "", "platform": "x"},
        {
            "title": "B",
            "body": "Cover is subject to policy terms. Speak to a specialist.",
            "cta": "Learn more",
            "platform": "x",
        },
    ]
    verdicts = evaluate_assets("jade", assets)
    assert set(verdicts.keys()) == {0, 1}
    assert verdicts[0]["status"] in ("fail", "needs_revision")


def test_summarize_verdicts():
    status, score = summarize_verdicts({"0": {"status": "pass", "score": 0.9}})
    assert status == "pass"
    assert score == 0.9

    status, _ = summarize_verdicts({"0": {"status": "fail", "score": 0.1}})
    assert status == "fail"

    status, _ = summarize_verdicts({})
    assert status == "unchecked"