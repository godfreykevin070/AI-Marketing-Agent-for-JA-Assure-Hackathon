"""Seed demo data: competitor baselines and starter lessons."""
from __future__ import annotations

import logging

from app.db import SessionLocal, init_db
from app.models import CompetitorSnapshot, Lesson

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEED_LESSONS = [
    {
        "brand": "jade",
        "platform": "linkedin",
        "reason_tag": "too_salesy",
        "text": "Keep the tone advisory and peer-to-peer; never pitch the policy directly.",
        "occurrences": 3,
    },
    {
        "brand": "doctorshield",
        "platform": "instagram",
        "reason_tag": "inaccurate_claim",
        "text": "Always qualify cover statements with 'subject to policy terms'.",
        "occurrences": 4,
    },
    {
        "brand": "jaguar_transit",
        "platform": "x",
        "reason_tag": "weak_hook",
        "text": "Open with a concrete operational scenario, not a generic value statement.",
        "occurrences": 2,
    },
]

SEED_COMPETITORS = [
    ("jade", "Regional Jewellers Block Provider A", "https://example.com/jewellers-block"),
    ("jaguar_transit", "Regional Cargo Insurer B", "https://example.com/cargo-cover"),
    ("doctorshield", "Regional Medical Indemnity Provider C", "https://example.com/indemnity"),
]

def ensure_default_admin() -> None:
    """Create the default admin if no users exist at all."""
    from app.config import get_settings
    from app.models import User
    from app.security import hash_password

    settings = get_settings()
    with SessionLocal() as db:
        if db.query(User).count() > 0:
            return
        admin = User(
            email=settings.default_admin_email.lower(),
            full_name=settings.default_admin_name,
            hashed_password=hash_password(settings.default_admin_password),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        logger.info("seeded default admin: %s", admin.email)

def seed() -> None:
    init_db()
    with SessionLocal() as db:
        if db.query(Lesson).count() == 0:
            for item in SEED_LESSONS:
                db.add(Lesson(**item))
            logger.info("seeded %s lessons", len(SEED_LESSONS))

        if db.query(CompetitorSnapshot).count() == 0:
            for brand, competitor, url in SEED_COMPETITORS:
                db.add(
                    CompetitorSnapshot(
                        brand=brand,
                        competitor=competitor,
                        url=url,
                        content_hash="seed",
                        snapshot={"excerpt": "seeded baseline", "length": 0},
                    )
                )
            logger.info("seeded %s competitor baselines", len(SEED_COMPETITORS))

        db.commit()
    logger.info("seed complete")


if __name__ == "__main__":
    seed()