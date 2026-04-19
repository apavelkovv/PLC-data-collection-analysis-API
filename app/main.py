from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.endpoints import (
    auth_router, users_router, stands_router,
    experiments_router, events_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="REST API for PLC telemetry collection, experiment management and user authorization",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(stands_router, prefix=API_PREFIX)
app.include_router(experiments_router, prefix=API_PREFIX)
app.include_router(events_router, prefix=API_PREFIX)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "app": settings.APP_TITLE, "version": settings.APP_VERSION}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
