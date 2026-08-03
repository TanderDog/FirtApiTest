from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_name: str = "mydb"
    db_user: str = "postgres"
    db_password: str
    db_port: int = 5432

    class Config:
        env_file = ".env"


settings = Settings()