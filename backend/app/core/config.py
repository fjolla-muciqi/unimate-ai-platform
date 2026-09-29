from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "UniMate AI"
    environment: str = "development"

    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Origjinat e lejuara për frontend-in (CORS).
    # Në .env jepen të ndara me presje.
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000"
    )

    upload_dir: str = "uploads/documents"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "document_chunks"
    embedding_model: str = (
        "sentence-transformers/"
        "paraphrase-multilingual-MiniLM-L12-v2"
    )

    # Sa chunks marrim nga Qdrant për çdo pyetje
    # dhe sa i ulët mund të jetë similarity score.
    rag_top_k: int = 5
    rag_min_score: float = 0.25

    # Madhësia e fragmenteve në karaktere; ndryshimi kërkon ri-indeksim.
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 120

    # Pesha e përputhjes së fjalëve te renditja hibride; 0 = vetëm vektorë.
    # 0.3 është fillimi i pllajës te `evaluation/hybrid_ablation.py`;
    # peshat më të larta fitojnë pak më shumë, por rrezikojnë t'u japin
    # fjalëve kyçe përparësi mbi kuptimin.
    rag_keyword_weight: float = 0.3

    anthropic_api_key: str | None = None
    llm_model: str = "claude-sonnet-5"
    llm_max_tokens: int = 8000
    llm_effort: str = "medium"

    # Sa herë mund të thërrasë modeli tools brenda një pyetjeje
    # të vetme para se ta ndalim ciklin agentik.
    agent_max_iterations: int = 6

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
