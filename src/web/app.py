from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from middlewares import RequestIDMiddleware
from web.lifespan import lifespan
from web.routes.health import router as health_router
from web.routes.telegram import router as telegram_router
from web.payments import router as payments_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Business Bot",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Роуты
    app.include_router(health_router)
    app.include_router(telegram_router)
    app.include_router(payments_router)
    app.add_middleware(RequestIDMiddleware)

    return app
