from pathlib import Path

from aiogram.enums import ParseMode
from pydantic import BaseModel, PostgresDsn, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]


# ========== NESTED CONFIGS ==========
class TelegramConfig(BaseModel):
    token: str
    parse_mode: ParseMode = ParseMode.HTML


class DataBaseConfig(BaseModel):
    # Храним «чистый» DSN без драйвера, а async-URL вычисляем отдельно
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 20
    max_overflow: int = 10

    @computed_field  # pydantic v2
    @property
    def async_url(self) -> str:
        """URL для SQLAlchemy async (postgresql+asyncpg)."""
        s = str(self.url)
        if s.startswith("postgres://"):
            s = s.replace("postgres://", "postgresql://", 1)
        if s.startswith("postgresql://"):
            s = s.replace("postgresql://", "postgresql+asyncpg://", 1)
        return s


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    decode_responses: bool = True  # вместо непонятного flag

    @computed_field
    @property
    def url(self) -> str:
        # Формируем redis://[:password]@host:port/db
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class PaymentConfig(BaseModel):
    tinkoff_terminal_key: str
    tinkoff_secret: str


class EmailConfig(BaseModel):
    host: str = "smtp.yandex.ru"
    port: int = 465
    name: str
    pwd: str


class AdminConfig(BaseModel):
    admin_id: int
    advertiser_id: int
    debug: bool = False


class WebConfig(BaseModel):
    port: int = 8080
    host: str = "0.0.0.0"
    base_url: str  # https://bot.example.com
    pay_path: str = "/telegram/pay"
    main_path: str = "/telegram/webhook"

    def get_webhook_url(self) -> str:
        base = self.base_url.rstrip("/")
        path = (
            self.main_path if self.main_path.startswith("/") else f"/{self.main_path}"
        )
        return f"{base}{path}"


# ========== ROOT SETTINGS ==========
class Settings(BaseSettings):
    """
    Загружает переменные из ENV и .env с вложенными префиксами.
    Пример: BOT_CONFIG__BOT__TOKEN=... -> settings.bot.token
    """

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=(str(BASE_DIR / ".env"),),
        env_nested_delimiter="__",
        env_prefix="BOT_CONFIG__",
        env_file_encoding="utf-8",
        validate_default=False,
    )

    main: AdminConfig
    db: DataBaseConfig
    redis: RedisConfig
    bot: TelegramConfig
    pay: PaymentConfig
    email: EmailConfig
    web: WebConfig

    # Мягкая валидация/нормализация: приводим base_url к https://...
    @field_validator("web")
    @classmethod
    def _normalize_base_url(cls, v: WebConfig) -> WebConfig:
        if not (v.base_url.startswith("http://") or v.base_url.startswith("https://")):
            v.base_url = f"https://{v.base_url}"
        return v


settings = Settings()
