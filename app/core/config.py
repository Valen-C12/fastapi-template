from pydantic_settings import BaseSettings

"""
Note:
DON'T store any sensitive information like user name and password in the code
Store such info in env config that will not pushed into git

referece:
- https://12factor.net/config
- https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure
"""


class Settings(BaseSettings):
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_user: str = ""
    pg_password: str = ""
    pg_database: str = "drawer"

    class Config:
        env_file = ".env"


settings = Settings()
