from dotenv import load_dotenv
import os
from urllib.parse import quote
from typing import Optional

load_dotenv()

class Settings:
    PROJECT_NAME: str = "APIUser"
    PROJECT_VERSION: str = "1.0.0"
    
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: Optional[str] = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "app_db")
    POSTGRES_PASSWORD_ENCODED: Optional[str] = quote(POSTGRES_PASSWORD) if POSTGRES_PASSWORD else None
    DATABASE_URL: str = (
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD_ENCODED}"
        f"@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
settings = Settings()


if __name__ == "__main__":
    print(f"Database URL: {settings.DATABASE_URL}")