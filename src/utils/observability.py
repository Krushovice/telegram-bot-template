import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration


def init_sentry(
    dsn: str | None, env: str = "prod", traces: float = 0.0, profiles: float = 0.0
):
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        environment=env,
        integrations=[
            FastApiIntegration(),
            LoggingIntegration(level=None, event_level=None),
            RedisIntegration(),
        ],
        traces_sample_rate=traces,
        profiles_sample_rate=profiles,
        send_default_pii=False,
        max_breadcrumbs=50,
    )
