"""Compliance gate — a first-class agent, not an afterthought.

Two layers:
  1. Deterministic regex pre-screen (fast, unmissable, auditable).
  2. LLM rubric evaluation against the 10-rule compliance rubric.
A verdict can only be `pass` if BOTH layers agree.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from app.agents.prompts import (
    BANNED_PATTERNS,
    COMPLIANCE_RULES,
    REQUIRED_DISCLAIMER_HINTS,
    brand_block,
    platform_block,
    rubric_block,
)
from app.enums import ComplianceStatus
from app.llm import chat_json, is_available
from app.schemas import ComplianceReport

logger = logging.getLogger(__name__)

COMPLIANCE_SYSTEM = (
    "You are a regulatory compliance reviewer for insurance marketing in "
    "Singapore, Malaysia, Hong Kong, Indonesia and Thailand. You are strict and "
    "sceptical. You flag anything that could be read as a guarantee, an "
    "unsubstantiated claim, a misleading absolute, or advice. When in doubt, you "
    "fail the asset and explain precisely why."
)

_COMPILED_BANNED = [(p, re.compile(p, re.IGNORECASE)) for p in BANNED_PATTERNS]


def deterministic_screen(asset: dict[str, Any]) -> dict[str, Any]:
    """Regex pre-screen. Returns a partial verdict dict."""
    haystack = " \n".join(
        str(asset.get(f) or "") for f in ("title", "hook", "body", "cta")
    )
    hits: list[str] = []
    spans: list[str] = []
    for pattern, rx in _COMPILED_BANNED:
        for m in rx.finditer(haystack):
            hits.append(f"C1/C2: prohibited phrase '{m.group(0)}'")
            spans.append(m.group(0))

    body = str(asset.get("body") or "").lower()
    references_cover = any(
        kw in body for kw in ("cover", "policy", "claim", "insured", "protection", "premium")
    )
    has_disclaimer = any(hint in body for hint in REQUIRED_DISCLAIMER_HINTS)
    if references_cover and not has_disclaimer:
        hits.append(
            "C6: references cover/policy/claims but carries no qualifying disclaimer "
            "(e.g. 'subject to policy terms')."
        )

    return {
        "deterministic_fail": bool(hits),
        "deterministic_reasons": hits,
        "deterministic_spans": spans,
    }


def _llm_verdicts(assets: list[dict[str, Any]], brand: str) -> dict[int, dict[str, Any]]:
    """One batched LLM call for up to ~12 assets."""
    if not is_available() or not assets:
        return {}

    payload = [
        {
            "asset_index": i,
            "platform": a.get("platform"),
            "title": a.get("title"),
            "hook": a.get("hook"),
            "body": a.get("body"),
            "cta": a.get("cta"),
            "hashtags": a.get("hashtags"),
        }
        for i, a in enumerate(assets)
    ]

    prompt = (
        f"{brand_block(brand)}\n"
        f"COMPLIANCE RUBRIC:\n{rubric_block()}\n\n"
        "Review every asset below against every rule in the rubric. "
        "For each asset return: asset_index, status ('pass' | 'needs_revision' | 'fail'), "
        "score (0-1), failed_rules (rule ids like 'C1'), reasons (plain English), "
        "offending_spans (the exact problematic phrases), and suggested_fix "
        "(a concrete rewrite instruction).\n"
        "Be strict. If an asset mentions cover without qualification, it fails C4/C6. "
        "If it uses any absolute or superlative, it fails C2/C3.\n\n"
        f"ASSETS:\n{payload}\n\nRespond as JSON with a `verdicts` array."
    )

    try:
        report: ComplianceReport = chat_json(
            COMPLIANCE_SYSTEM, prompt, ComplianceReport, temperature=0.1
        )
    except Exception as exc:
        logger.warning("compliance LLM failed: %s", exc)
        return {}

    return {v.asset_index: v.model_dump(mode="json") for v in report.verdicts}


def evaluate_assets(brand: str, assets: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Full compliance evaluation. Returns {asset_index: verdict}."""
    results: dict[int, dict[str, Any]] = {}

    # Batch to keep prompts within token limits.
    batch_size = 12
    llm_results: dict[int, dict[str, Any]] = {}
    for start in range(0, len(assets), batch_size):
        chunk = assets[start : start + batch_size]
        for idx, verdict in _llm_verdicts(chunk, brand).items():
            llm_results[start + idx] = verdict

    for i, asset in enumerate(assets):
        det = deterministic_screen(asset)
        llm = llm_results.get(i)

        if llm is None:
            status = (
                ComplianceStatus.fail.value
                if det["deterministic_fail"]
                else ComplianceStatus.needs_revision.value
            )
            results[i] = {
                "status": status,
                "score": 0.0 if det["deterministic_fail"] else 0.5,
                "failed_rules": ["C1"] if det["deterministic_fail"] else [],
                "reasons": det["deterministic_reasons"]
                or ["Automated LLM review unavailable — manual review required."],
                "offending_spans": det["deterministic_spans"],
                "suggested_fix": "Remove prohibited claims and add a policy-terms qualifier.",
                "layer": "deterministic_only",
            }
            continue

        reasons = list(llm.get("reasons", []))
        spans = list(llm.get("offending_spans", []))
        failed_rules = list(llm.get("failed_rules", []))
        score = float(llm.get("score", 0.5))
        status = str(llm.get("status", "needs_revision"))

        if det["deterministic_fail"]:
            status = ComplianceStatus.fail.value
            reasons = det["deterministic_reasons"] + reasons
            spans = det["deterministic_spans"] + spans
            failed_rules = sorted(set(failed_rules + ["C1"]))
            score = min(score, 0.2)

        results[i] = {
            "status": status,
            "score": round(score, 3),
            "failed_rules": failed_rules,
            "reasons": reasons,
            "offending_spans": spans,
            "suggested_fix": llm.get("suggested_fix", ""),
            "layer": "deterministic+llm",
        }

    return results


def compliance_node(state: dict) -> dict:
    """LangGraph node: gate every draft."""
    drafts = state.get("drafts", [])
    if not state.get("auto_compliance", True) or not drafts:
        return {"compliance": state.get("compliance", {})}

    errors = list(state.get("errors", []))
    try:
        verdicts = evaluate_assets(state["brand"], drafts)
    except Exception as exc:
        logger.exception("compliance node failed")
        errors.append(f"compliance: {exc}")
        verdicts = {
            i: {
                "status": ComplianceStatus.needs_revision.value,
                "score": 0.0,
                "failed_rules": [],
                "reasons": [f"Compliance evaluation error: {exc}"],
                "offending_spans": [],
                "suggested_fix": "Manual review required.",
                "layer": "error",
            }
            for i in range(len(drafts))
        }

    return {"compliance": {str(k): v for k, v in verdicts.items()}, "errors": errors}


def summarize_verdicts(verdicts: dict[str, dict[str, Any]]) -> tuple[str, float]:
    """Collapse per-asset verdicts into an asset-level status + score."""
    if not verdicts:
        return ComplianceStatus.unchecked.value, 0.0
    statuses = [v.get("status") for v in verdicts.values()]
    scores = [float(v.get("score", 0)) for v in verdicts.values()]
    avg = sum(scores) / len(scores) if scores else 0.0
    if all(s == "pass" for s in statuses):
        return ComplianceStatus.pass_.value, round(avg, 3)
    if any(s == "fail" for s in statuses):
        return ComplianceStatus.fail.value, round(avg, 3)
    return ComplianceStatus.needs_revision.value, round(avg, 3)