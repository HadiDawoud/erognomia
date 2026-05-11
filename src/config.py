from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Ergonomia"
    debug: bool = True

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8001

    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:latest"

    # Vector Store Configuration
    chroma_persist_dir: str = "./data/chroma"
    embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

    # Ingestion Configuration
    target_site_url: str = "https://immersive-reality-lab.de"
    max_crawl_depth: int = 5
    max_pages: int = 800
    crawl_polite_delay_sec: float = 0.35
    chunk_size: int = 1000
    chunk_overlap: int = 200

    scraped_snapshot_dir: str = "./data/scraped"
    extra_seed_urls: str = ""

    # RAG Configuration
    retrieval_k: int = 8
    retrieval_max_distance: float = 0.62

    @property
    def extra_seed_urls_list(self) -> List[str]:
        return [part.strip() for part in self.extra_seed_urls.replace("\n", ",").split(",") if part.strip()]

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

# Ensure directories exist
Path(settings.chroma_persist_dir).parent.mkdir(parents=True, exist_ok=True)
Path(settings.scraped_snapshot_dir).mkdir(parents=True, exist_ok=True)
