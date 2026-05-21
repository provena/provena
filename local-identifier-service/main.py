"""
Local Identifier Service - On-prem replacement for ARDC Handle Service.
Provides handle minting and resolution via PostgreSQL.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from routes import handle_routes, resolve_routes

app = FastAPI(title="Local Identifier Service", version="1.0.0")

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(handle_routes.router, prefix="/handle", tags=["Handle"])
app.include_router(resolve_routes.router, prefix="/resolve", tags=["Resolve"])


@app.get("/")
async def root():
    return {"service": "local-identifier-service", "status": "ok"}
