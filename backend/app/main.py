from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import approver, auth, bank_requests, dashboard

# Creates tables on startup if they don't exist yet (simple approach, no migrations tool).
Base.metadata.create_all(bind=engine)

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


@app.get("/")
def root():
    return {"status": "ok"}
