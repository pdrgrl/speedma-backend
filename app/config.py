from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str
    embed_model: str = "gemini-embedding-001"
    gen_model: str = "gemini-2.5-flash-lite"
    chroma_path: str = "./chroma_db"
    graph_path: str = "./graph/static_graph.json"
    corpus_path: str = "./corpus"
    top_k: int = 6

settings = Settings()