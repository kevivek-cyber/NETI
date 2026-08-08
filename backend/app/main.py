"""
NETI FastAPI Application Entrypoint.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.ceremony_router import router as ceremony_router
from app.api.exam_router import router as exam_router

app = FastAPI(
    title="NETI — Non-Exploitable Test Integrity API",
    description="Zero pre-exam question persistence & public Merkle audit ledger engine.",
    version="0.1.0",
)

# Only needed when the Vite dev server runs on a different port. In a
# deployed build everything is same-origin and this grants nothing.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("NETI_CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

# CORS middleware for React kiosk & invigilator admin console
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers under /api
app.include_router(ceremony_router, prefix="/api")
app.include_router(exam_router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "neti-backend",
        "version": "0.1.0",
    }

# Serve the built exam client from this same process, so the whole thing
# is one service on one origin. Absent in dev — run `npm run dev` and let
# Vite proxy /api here instead.
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="web")
