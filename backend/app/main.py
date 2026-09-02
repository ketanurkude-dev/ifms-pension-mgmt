from datetime import date, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Announcement, Faq
from app.routers import (
    announcements,
    approver,
    arrears,
    auth,
    bank_requests,
    dashboard,
    disbursements,
    grievances,
    life_certificate,
    pension,
    requests,
    tax,
)

# Creates tables on startup if they don't exist yet (simple approach, no migrations tool).
Base.metadata.create_all(bind=engine)


def _seed_announcements_and_faqs() -> None:
    """One-time seed for content that isn't per-pensioner, so the
    Announcements page has something to show without an officer having
    to create it first."""
    db = SessionLocal()
    try:
        if db.query(Announcement).count() == 0:
            today = date.today()
            db.add_all(
                [
                    Announcement(
                        title="Revised dearness relief rate effective this quarter",
                        body="The dearness relief rate applicable to pensions has been revised per the latest "
                        "Finance Department order. The revised rate will reflect in the pension slip for the "
                        "current month.",
                        category="Policy",
                        valid_from=today - timedelta(days=5),
                        valid_to=today + timedelta(days=60),
                        status="Published",
                        published_at=today - timedelta(days=5),
                    ),
                    Announcement(
                        title="Portal maintenance window this weekend",
                        body="The Pensioner Portal will be unavailable from 11 PM Saturday to 5 AM Sunday for "
                        "scheduled maintenance. Pension disbursement is not affected.",
                        category="Outage / maintenance",
                        valid_from=today - timedelta(days=2),
                        valid_to=today + timedelta(days=5),
                        status="Published",
                        published_at=today - timedelta(days=2),
                    ),
                ]
            )
        if db.query(Faq).count() == 0:
            db.add_all(
                [
                    Faq(
                        question="How do I download my pension slip?",
                        answer="Go to Pension Slip in the left menu, choose the month, and click Download.",
                        category="Pension slip",
                        display_order=1,
                    ),
                    Faq(
                        question="Whom do I contact if my pension is not credited?",
                        answer="Lodge a grievance under the category 'Non-receipt or short receipt of pension' "
                        "from the Grievances page. It is routed to the concerned officer automatically.",
                        category="Payments",
                        display_order=1,
                    ),
                    Faq(
                        question="How do I update my bank account details?",
                        answer="Go to Bank details and submit a bank account change request. It takes effect "
                        "once your pension officer approves it.",
                        category="Bank details",
                        display_order=1,
                    ),
                ]
            )
        db.commit()
    finally:
        db.close()


_seed_announcements_and_faqs()

app = FastAPI(title="Pensioner Portal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(bank_requests.router)
app.include_router(approver.router)
app.include_router(pension.router)
app.include_router(disbursements.router)
app.include_router(tax.router)
app.include_router(grievances.router)
app.include_router(requests.router)
app.include_router(arrears.router)
app.include_router(announcements.router)
app.include_router(life_certificate.router)


@app.get("/")
def root():
    return {"status": "ok"}
