from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = Field(default="chatbot_rag", alias="APP_NAME")
    environment: str = Field(default="local", alias="ENVIRONMENT")
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")

    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_chat_model: str = Field(default="hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M", alias="OLLAMA_CHAT_MODEL")
    ollama_embed_model: str = Field(default="bge-m3", alias="OLLAMA_EMBED_MODEL")
    ollama_request_timeout: float = Field(default=120.0, alias="OLLAMA_REQUEST_TIMEOUT")
    llm_temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE")
    llm_num_predict: int = Field(default=256, alias="LLM_NUM_PREDICT")
    llm_think: bool = Field(default=False, alias="LLM_THINK")
    ollama_keep_alive: str = Field(default="10m", alias="OLLAMA_KEEP_ALIVE")

    chroma_path: Path = Field(default=PROJECT_ROOT / "data" / "vector_store" / "chroma", alias="CHROMA_PATH")
    chroma_collection: str = Field(default="manual_documents", alias="CHROMA_COLLECTION")

    database_url: str = Field(default="sqlite:///./data/app.sqlite3", alias="DATABASE_URL")

    raw_data_path: Path = Field(default=PROJECT_ROOT / "data" / "raw", alias="RAW_DATA_PATH")
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, alias="CHUNK_OVERLAP")
    embedding_batch_size: int = Field(default=16, alias="EMBEDDING_BATCH_SIZE")

    top_k: int = Field(default=5, alias="TOP_K")

    tour_api_service_key: str | None = Field(default=None, alias="TOUR_API_SERVICE_KEY")
    tour_api_accessible_service_key: str | None = Field(default=None, alias="TOUR_API_ACCESSIBLE_SERVICE_KEY")
    tour_api_base_url: str = Field(default="https://apis.data.go.kr/B551011/KorService2", alias="TOUR_API_BASE_URL")
    tour_api_accessible_base_url: str = Field(
        default="https://apis.data.go.kr/B551011/KorWithService2",
        alias="TOUR_API_ACCESSIBLE_BASE_URL",
    )
    tour_api_mobile_os: str = Field(default="ETC", alias="TOUR_API_MOBILE_OS")
    tour_api_mobile_app: str = Field(default="chatbot_rag", alias="TOUR_API_MOBILE_APP")
    tour_api_timeout: float = Field(default=20.0, alias="TOUR_API_TIMEOUT")
    tourism_sample_path: Path = Field(default=PROJECT_ROOT / "data" / "raw" / "tourism_accessible", alias="TOURISM_SAMPLE_PATH")

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def resolved_chroma_path(self) -> Path:
        return self._resolve_project_path(self.chroma_path)

    @property
    def resolved_raw_data_path(self) -> Path:
        return self._resolve_project_path(self.raw_data_path)

    @property
    def resolved_tourism_sample_path(self) -> Path:
        return self._resolve_project_path(self.tourism_sample_path)

    @staticmethod
    def _resolve_project_path(path: Path) -> Path:
        if path.is_absolute():
            return path
        return PROJECT_ROOT / path

    @property
    def cors_origin_list(self) -> List[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def prompt_path(self) -> Path:
        return PROJECT_ROOT / "prompts" / "rag_answer_prompt.txt"

    @property
    def no_context_prompt_path(self) -> Path:
        return PROJECT_ROOT / "prompts" / "no_context_prompt.txt"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
