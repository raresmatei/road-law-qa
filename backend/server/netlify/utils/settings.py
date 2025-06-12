from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    PINECONE_API_KEY: str
    PINECONE_ENV: str
    PINECONE_INDEX: str
    JWT_SECRET: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DATABASE_URL: str
    ADMIN_USERNAME: str
    ADMIN_PASSWORD_HASH: str  # bcrypt‐hash of the admin’s password

    class Config:
        env_file = ".env"

settings = Settings()