"""Brand voices, platform specs and the compliance rubric.

This module is deliberately data-heavy: prompts are configuration, and the
quality of the whole system lives here.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Brand voices
# ---------------------------------------------------------------------------
BRAND_VOICES: dict[str, dict[str, str]] = {
    "jade": {
        "name": "Jade",
        "product": "Jewellers block insurance (all-risks cover for stock, transit, "
                   "display and customer's goods held in trust).",
        "audience": "Jewellery retailers, pawnbrokers, gem and precious-metal dealers, "
                    "watch boutiques in Singapore, Malaysia and Hong Kong.",
        "tone": "Elegant, understated, quietly expert. Speaks peer-to-peer with a "
                "shop owner who has 30 years in the trade. Never hyped, never "
                "discount-driven. Confidence without bravado.",
        "signature": "Discreet protection for what you've built. Precision over promises.",
        "do": [
            "Use trade-accurate language (block cover, memorandum, transit extension).",
            "Reference real risks: valuation drift, staff handling, exhibition loans.",
            "Reassure with process, not with guarantees.",
        ],
        "dont": [
            "Never use discount or 'cheapest' language.",
            "Never imply claims are always paid.",
            "Avoid retail-consumer phrasing ('protect your precious memories').",
        ],
    },
    "jaguar_transit": {
        "name": "Jaguar Transit",
        "product": "Cargo / goods-in-transit insurance for high-value consignments "
                   "(electronics, luxury goods, bullion, art, pharmaceuticals).",
        "audience": "Freight forwarders, couriers, 3PL operators, e-commerce "
                    "fulfilment firms and their risk managers.",
        "tone": "Operational, precise, logistics-fluent. Speaks in corridors, "
                "incoterms and dwell times. Confident and practical.",
        "signature": "Every leg covered. Every handover documented.",
        "do": [
            "Use logistics vocabulary: last mile, CIF, handover, seal integrity.",
            "Frame cover around operational continuity, not fear.",
            "Talk about SLAs and claims turnaround processes.",
        ],
        "dont": [
            "Never promise zero loss or guaranteed claim payouts.",
            "Avoid consumer-romance language about 'precious items'.",
        ],
    },
    "doctorshield": {
        "name": "DoctorShield",
        "product": "Medical indemnity / professional indemnity for doctors, clinics "
                   "and allied health practitioners.",
        "audience": "GPs, specialists, dental practices, aesthetic clinics and "
                    "clinic managers across SG, MY, HK, ID and TH.",
        "tone": "Calm, clinical, collegial. A senior colleague explaining risk, not "
                "a broker selling a policy. Compliance-first and non-alarmist.",
        "signature": "Practice with certainty. Defined protection, clearly explained.",
        "do": [
            "Use clinical and medico-legal vocabulary accurately.",
            "Explain what is and is not covered, in plain language.",
            "Acknowledge the regulatory environment (MOH, MMC, DCHK).",
        ],
        "dont": [
            "Never give clinical advice or imply legal advice.",
            "Never guarantee indemnity outcomes or claim amounts.",
            "Never use fear-based malpractice scare tactics.",
        ],
    },
    "ja_assure": {
        "name": "JA Assure",
        "product": "InsurTech group offering specialist cover across the region.",
        "audience": "Brokers, partners and SME decision-makers across SEA.",
        "tone": "Confident, modern, technology-forward. Explains complex cover simply.",
        "signature": "Specialist cover, built for how you actually operate.",
        "do": ["Lead with the customer problem.", "Show the technology advantage."],
        "dont": ["Never guarantee underwriting outcomes."],
    },
}

DEFAULT_BRAND = "ja_assure"


# ---------------------------------------------------------------------------
# Platform specs
# ---------------------------------------------------------------------------
PLATFORM_SPECS: dict[str, dict[str, str | int]] = {
    "linkedin": {
        "max_chars": 2900,
        "style": "Professional, longer-form. Opens with a credible insight, not a hook.",
        "structure": "Insight → context/problem → JA perspective → soft CTA. "
                     "Short paragraphs, 1-2 sentences each. 3-5 hashtags.",
        "format": "post",
    },
    "instagram": {
        "max_chars": 2200,
        "style": "Visual-first. The caption supports the image/carousel.",
        "structure": "Scroll-stopping first line → 3-5 short value bullets → CTA → "
                     "hashtag block (8-15 tags).",
        "format": "caption",
    },
    "x": {
        "max_chars": 280,
        "style": "Hook-first, punchy, one idea per post.",
        "structure": "Hook line → single insight → CTA or link placeholder. 1-2 tags.",
        "format": "post",
    },
    "tiktok": {
        "max_chars": 2200,
        "style": "Conversational, on-camera script feel, native and unpolished.",
        "structure": "3-second hook → payoff → CTA. Written as a spoken script.",
        "format": "reel",
    },
    "blog": {
        "max_chars": 12000,
        "style": "SEO-aware long form with H2 subheads and a clear thesis.",
        "structure": "H1 → intro → 3-5 H2 sections → conclusion → CTA.",
        "format": "blog",
    },
}


# ---------------------------------------------------------------------------
# Compliance rubric — the gate every asset must pass
# ---------------------------------------------------------------------------
COMPLIANCE_RULES: list[dict[str, str]] = [
    {
        "id": "C1",
        "name": "No guarantees or promises",
        "detail": "Must not guarantee cover, payout, claim acceptance, approval, "
                  "returns or outcomes. Words like 'guaranteed', 'assured', "
                  "'certain to pay', 'risk-free' are prohibited.",
    },
    {
        "id": "C2",
        "name": "No misleading absolutes",
        "detail": "Must not claim '100% cover', 'fully covered', 'total protection', "
                  "'complete peace of mind' or similar absolutes without qualification.",
    },
    {
        "id": "C3",
        "name": "No unsubstantiated superlatives",
        "detail": "Must not claim 'best', 'cheapest', '#1', 'leading' or "
                  "'most trusted' without a verifiable, cited basis.",
    },
    {
        "id": "C4",
        "name": "Cover terms must be accurate and qualified",
        "detail": "Any mention of cover must be consistent with a typical policy "
                  "structure and must include a qualifier such as 'subject to policy "
                  "terms', 'typically', or 'depending on your policy'.",
    },
    {
        "id": "C5",
        "name": "No clinical, legal or tax advice",
        "detail": "Especially for DoctorShield: must not give medical, legal or tax "
                  "advice, and must not imply medico-legal representation.",
    },
    {
        "id": "C6",
        "name": "Appropriate disclaimers",
        "detail": "Assets referencing cover, pricing or claims must carry an "
                  "appropriate disclaimer or a pointer to full policy terms.",
    },
    {
        "id": "C7",
        "name": "Brand voice integrity",
        "detail": "Must match the assigned brand voice: Jade = discreet and expert; "
                  "Jaguar Transit = operational and precise; DoctorShield = calm and "
                  "clinical. No hype, no discount language, no fear-mongering.",
    },
    {
        "id": "C8",
        "name": "No prohibited data or PII",
        "detail": "Must not include personal data of third parties, real claim "
                  "anecdotes with identifying detail, or client names without consent.",
    },
    {
        "id": "C9",
        "name": "Platform compliance",
        "detail": "Must respect platform constraints (character limits, no misleading "
                  "financial promotions) and local advertising standards in the target "
                  "market.",
    },
    {
        "id": "C10",
        "name": "No discriminatory or fear-based targeting",
        "detail": "Must not exploit fear, or target protected characteristics.",
    },
]

# Fast deterministic pre-screen. Any hit forces a non-pass verdict even if the
# LLM misses it — belt and braces for a regulated domain.
BANNED_PATTERNS: list[str] = [
    r"\bguarantee(d|s)?\b",
    r"\bwe will pay\b",
    r"\b100%\s*(cover|covered|payout|protection)\b",
    r"\bfully covered\b",
    r"\brisk[\s-]?free\b",
    r"\bno risk\b",
    r"\bassured returns?\b",
    r"\bcheapest\b",
    r"\bbest in the market\b",
    r"\bnumber one\b",
    r"\b#1\b",
    r"\bsure payout\b",
    r"\bclaim is confirmed\b",
    r"\btotal protection\b",
    r"\bcomplete peace of mind\b",
]

REQUIRED_DISCLAIMER_HINTS: list[str] = [
    "subject to",
    "terms and conditions",
    "policy terms",
    "terms apply",
    "full policy",
    "depending on your policy",
    "typically",
]


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------
def brand_block(brand: str) -> str:
    v = BRAND_VOICES.get(brand, BRAND_VOICES[DEFAULT_BRAND])
    do = "\n".join(f"  - {x}" for x in v["do"])
    dont = "\n".join(f"  - {x}" for x in v["dont"])
    return (
        f"BRAND: {v['name']}\n"
        f"PRODUCT: {v['product']}\n"
        f"AUDIENCE: {v['audience']}\n"
        f"TONE: {v['tone']}\n"
        f"SIGNATURE LINE: {v['signature']}\n"
        f"DO:\n{do}\n"
        f"DO NOT:\n{dont}\n"
    )


def platform_block(platform: str) -> str:
    spec = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["linkedin"])
    return (
        f"PLATFORM: {platform}\n"
        f"STYLE: {spec['style']}\n"
        f"STRUCTURE: {spec['structure']}\n"
        f"CHARACTER LIMIT: {spec['max_chars']}\n"
    )


def rubric_block() -> str:
    lines = [f"[{r['id']}] {r['name']}: {r['detail']}" for r in COMPLIANCE_RULES]
    return "\n".join(lines)


def lessons_block(lessons: list[dict]) -> str:
    if not lessons:
        return ""
    lines = [
        f"- ({l.get('reason_tag') or 'general'}) {l.get('text')}"
        + (f" [seen {l['occurrences']}x]" if l.get("occurrences") else "")
        for l in lessons
    ]
    return (
        "PAST HUMAN CORRECTIONS — these are real edits/rejections from our reviewers.\n"
        "Do NOT repeat these mistakes:\n" + "\n".join(lines) + "\n"
    )