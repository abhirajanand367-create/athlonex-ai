from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Athlonex AI Service"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    model_path: str = "models"
    upload_dir: str = "/tmp/athlonex-uploads"
    max_video_size_mb: int = 500

    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    s3_bucket: Optional[str] = None
    s3_region: str = "us-east-1"

    jwt_secret: str = "athlonex-ai-service-secret"
    allowed_origins: str = "http://localhost:3000,http://localhost:5000"

    class Config:
        env_file = ".env"
        env_prefix = "AI_"


settings = Settings()
