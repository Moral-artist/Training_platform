from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from typing import Literal

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str
    IS_PRODUCTION: str = "development"
    SESSION_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_SSL: bool = False

    # PLAYBACK_TOKEN_SECRET=<单独生成的高强度随机密钥>
    # VIDEO_WORKER_BASE_URL=https://<你的-Worker-域名>
    PLAYBACK_TOKEN_SECRET: str = ""
    VIDEO_WORKER_BASE_URL: str = ""
    PLAYBACK_TOKEN_TTL: int = 300
    REDIS_URL: str = "redis://localhost:6380/0"
    R2_ENDPOINT: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET: str
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    TRANSCODE_TIMEOUT_SECONDS: int = 7200
    # 4K 源文件使用分段上传；旧单文件接口继续限制 300 MiB。
    MAX_UPLOAD_BYTES: int = 8 * 1024 * 1024 * 1024
    UPLOAD_PART_BYTES: int = 16 * 1024 * 1024
    UPLOAD_RETENTION_HOURS: int = 48
    HLS_HEIGHTS: str = "720,1080,1440,2160"
    HLS_CRF: int = 21
    HLS_PRESET: str = "medium"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
