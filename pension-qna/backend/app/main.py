from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.rooms import router as rooms_router
from app.db import models  # noqa: F401 - registers SQLAlchemy metadata
from app.db.session import Base, engine

app = FastAPI(title="Pension Reservation QnA")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(rooms_router)


@app.on_event("startup")
def create_schema() -> None:
    Base.metadata.create_all(engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
