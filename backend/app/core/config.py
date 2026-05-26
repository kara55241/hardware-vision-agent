from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    lm_studio_url: str = "http://localhost:1234/v1"
    vlm_model: str = "gemma-3-12b"
    text_model: str = "phi-4-14b"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    upload_dir: str = "data/uploads"
    yolo_model_path: str = "data/yolo_models/best.pt"
    chromadb_path: str = "data/chromadb"

settings = Settings()
