from uvicorn import run as uvicorn_run
from web.app import create_app
from core.config import settings

app = create_app()

if __name__ == "__main__":
    uvicorn_run(
        "src.main:app",
        host=settings.web.host,
        port=settings.web.port,
        log_level="info",
        reload=True,  # убери на проде
    )
