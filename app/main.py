from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.endpoints import (
    auth_router, users_router, stands_router,
    experiments_router, events_router,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Логика при старте и завершении приложения
    yield

# 1. Создаем ОДИН экземпляр приложения со всеми настройками сразу
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="REST API for PLC telemetry collection, experiment management and user authorization",
    lifespan=lifespan,
)

# 2. Настраиваем CORS (одного раза достаточно)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Монтируем статику ДО подключения роутеров
# Убедитесь, что папка 'static' находится в корне проекта, там же где main.py
app.mount("/static", StaticFiles(directory="static"), name="static")

# 4. Подключаем роутеры
API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(stands_router, prefix=API_PREFIX)
app.include_router(experiments_router, prefix=API_PREFIX)
app.include_router(events_router, prefix=API_PREFIX)

# 5. Базовые эндпоинты
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "app": settings.APP_TITLE, "version": settings.APP_VERSION}

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}