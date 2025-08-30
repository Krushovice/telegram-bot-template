import logging, os, sys, re, time
from typing import Iterable

import structlog

DEFAULT_MASK_KEYS = {
    "authorization",
    "token",
    "password",
    "pwd",
    "secret",
    "api_key",
    "set-cookie",
}


def _mask_kv(_, __, event_dict: dict):
    def mask_value(value: str):
        if not isinstance(value, str):
            return value
        if len(value) <= 8:
            return "******"
        return value[:4] + "******" + value[-2:]

    lowered = {k.lower(): k for k in event_dict.keys()}
    for lk, orig in lowered.items():
        if lk in DEFAULT_MASK_KEYS:
            event_dict[orig] = mask_value(str(event_dict[orig]))
    return event_dict


def _add_process_time(_, __, event_dict: dict):
    event_dict.setdefault("ts", int(time.time() * 1000))
    return event_dict


def setup_logging(
    service: str = "business-bot",
    env: str | None = None,
    json_logs: bool | None = None,
    level: str = "INFO",
):
    env = env or os.getenv("APP_ENV", "prod")
    json_logs = json_logs if json_logs is not None else (env != "dev")

    # stdlib logging
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        stream=sys.stdout,
        format="%(message)s",  # structlog сам отформатирует
    )
    for noisy in ("uvicorn", "uvicorn.error", "uvicorn.access", "asyncio", "aiogram"):
        logging.getLogger(noisy).setLevel(logging.INFO)

    shared_processors: Iterable = [
        structlog.contextvars.merge_contextvars,
        _add_process_time,
        _mask_kv,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        structlog.processors.EventRenamer("message"),
        structlog.processors.add_log_level,
        structlog.stdlib.add_logger_name,
    ]

    if json_logs:
        renderer = structlog.processors.JSONRenderer(sort_keys=False)
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
        wrapper_class=structlog.stdlib.BoundLogger,
    )

    # Базовый контекст
    logger = structlog.get_logger().bind(service=service, env=env)
    logger.info(
        "logging_initialized",
        json=json_logs,
        level=level,
        env=env,
    )
    return logger


def get_logger(name: str = None):
    return structlog.get_logger(name or "app")
