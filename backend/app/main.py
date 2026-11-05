from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from .core.config import settings
from .core.security import hash_password
from .db import Base, engine, SessionLocal
from .models.entities import User
from .api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.app_env == "production":
        if settings.secret_key == "change-this-development-secret-before-deployment" or len(settings.secret_key) < 32:
            raise RuntimeError("Production requires a unique SECRET_KEY of at least 32 characters.")
        if not settings.admin_email or not settings.admin_password or len(settings.admin_password) < 14:
            raise RuntimeError("Production requires ADMIN_EMAIL and an ADMIN_PASSWORD of at least 14 characters.")
    settings.media_path.mkdir(parents=True, exist_ok=True)
    if engine.dialect.name == "postgresql":
        try:
            with engine.begin() as connection:
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        except Exception:
            # Database startup remains possible, but spatial duplicate checks will use the fallback path.
            pass
    if settings.app_env != "production":
        Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "postgresql":
        try:
            with engine.begin() as connection:
                connection.execute(text("CREATE INDEX IF NOT EXISTS ix_civic_issue_geog ON civic_issues USING GIST ((ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography))"))
        except Exception:
            pass
    if settings.admin_email and settings.admin_password:
        with SessionLocal() as db:
            existing = db.scalar(select(User).where(User.email == settings.admin_email.lower()))
            if not existing:
                db.add(User(email=settings.admin_email.lower(), password_hash=hash_password(settings.admin_password), role="admin", display_name="CIVIC-I Administrator"))
                db.commit()
    yield

app = FastAPI(title=settings.app_name, version="0.1.0", description="Civic issue reporting, two-class computer vision integration and priority assessment for Palghar.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])
app.include_router(router)

@app.get("/")
def root():
    return {"name": "CIVIC-I API", "status": "running", "scope": ["pothole", "garbage_accumulation"], "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok", "model": __import__("app.services.detector", fromlist=["detector"]).detector.status}
