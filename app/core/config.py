from pydantic_settings import BaseSettings

"""
Note:
DON'T store any sensitive information like user name and password in the code
Store such info in env config that will not pushed into git

reference:
- https://12factor.net/config
- https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure
"""


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database configuration
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_user: str = ""
    pg_password: str = ""
    pg_database: str = "drawer"

    # Redis configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_max_connections: int = 10

    # S3 configuration
    s3_endpoint_url: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_region: str = "us-east-1"
    s3_bucket_name: str = ""

    # Application configuration
    app_name: str = "FastAPI Template"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
