from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseModel):
    API_KEY: str
    SERVICE_NAME: str = "Payment Processing Service"
    ROOT_PATH: str = "/"
    DEBUG_MODE: bool = True
    LOGGING_LEVEL: str = "INFO"

    PROCESSING_LEASE_SECONDS: int = 30


class PostgresSettings(BaseModel):
    DB: str
    HOST: str
    PORT: int
    USER: str
    PASSWORD: str

    @property
    def dsn(self) -> str:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.USER,
            password=self.PASSWORD,
            host=self.HOST,
            port=self.PORT,
            path=f"{self.DB}",
        ).unicode_string()


class RabbitMQSettings(BaseModel):
    USER: str
    PASSWORD: str
    HOST: str = "rabbitmq"
    PORT: int = 5672
    VHOST: str = "/"

    @property
    def dsn(self) -> str:
        return (
            f"amqp://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.VHOST}"
        )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app: AppSettings
    postgres: PostgresSettings
    rabbitmq: RabbitMQSettings


settings = Settings()
