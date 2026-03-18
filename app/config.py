from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str
    debug: bool
    db_name: str
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    app_name: str
    app_description: str
    app_version: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    class Config:
        env_file = ".env"

settings = Settings()