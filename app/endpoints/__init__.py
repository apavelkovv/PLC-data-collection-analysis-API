from app.endpoints.auth import router as auth_router
from app.endpoints.users import router as users_router
from app.endpoints.stands import router as stands_router
from app.endpoints.experiments import router as experiments_router
from app.endpoints.events import router as events_router

__all__ = ["auth_router", "users_router", "stands_router", "experiments_router", "events_router"]
