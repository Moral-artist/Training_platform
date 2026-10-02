from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # PLAYBACK_TOKEN_SECRET=<单独生成的高强度随机密钥>
    # VIDEO_WORKER_BASE_URL=https://<你的-Worker-域名>
    PLAYBACK_TOKEN_SECRET: str = ""
    VIDEO_WORKER_BASE_URL: str = ""
    PLAYBACK_TOKEN_TTL: int = 300
    REDIS_URL: str = "redis://localhost:6380/0"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    TRANSCODE_TIMEOUT_SECONDS: int = 7200


    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
