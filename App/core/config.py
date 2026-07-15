import os


class Settings:
    app_name: str = os.getenv("APP_NAME", "FinRelief AI")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./finrelief.db")


settings = Settings()
