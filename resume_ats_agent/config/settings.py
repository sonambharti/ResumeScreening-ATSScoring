import os
from dotenv import load_dotenv

class Settings:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Settings, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        load_dotenv()
        
        # Load API keys from environment
        self._openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self._gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self._groq_api_key = os.getenv("GROQ_API_KEY", "")
        
        # Setup defaults
        self._default_llm_provider = os.getenv("DEFAULT_LLM_PROVIDER", "openai").lower()
        self._default_model_name = os.getenv("DEFAULT_MODEL_NAME", "gpt-4o")
        
        self._embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
        self._embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
        
        self._vector_db_dir = os.getenv("VECTOR_DB_DIR", "./data/vector_db")
        self._log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Scoring weights
        self.default_weights = {
            "skills": 0.40,
            "experience": 0.35,
            "education": 0.15,
            "certifications": 0.10
        }
        
        # Set OS environment variables for langchain integration
        if self._openai_api_key:
            os.environ["OPENAI_API_KEY"] = self._openai_api_key
        if self._gemini_api_key:
            os.environ["GEMINI_API_KEY"] = self._gemini_api_key
        if self._groq_api_key:
            os.environ["GROQ_API_KEY"] = self._groq_api_key
            
        self._initialized = True

    @property
    def openai_api_key(self) -> str:
        return self._openai_api_key

    @openai_api_key.setter
    def openai_api_key(self, value: str):
        self._openai_api_key = value.strip()
        os.environ["OPENAI_API_KEY"] = self._openai_api_key

    @property
    def gemini_api_key(self) -> str:
        return self._gemini_api_key

    @gemini_api_key.setter
    def gemini_api_key(self, value: str):
        self._gemini_api_key = value.strip()
        os.environ["GEMINI_API_KEY"] = self._gemini_api_key

    @property
    def groq_api_key(self) -> str:
        return self._groq_api_key

    @groq_api_key.setter
    def groq_api_key(self, value: str):
        self._groq_api_key = value.strip()
        os.environ["GROQ_API_KEY"] = self._groq_api_key

    @property
    def default_llm_provider(self) -> str:
        return self._default_llm_provider

    @default_llm_provider.setter
    def default_llm_provider(self, value: str):
        self._default_llm_provider = value.strip().lower()

    @property
    def default_model_name(self) -> str:
        return self._default_model_name

    @default_model_name.setter
    def default_model_name(self, value: str):
        self._default_model_name = value.strip()

    @property
    def embedding_provider(self) -> str:
        return self._embedding_provider

    @embedding_provider.setter
    def embedding_provider(self, value: str):
        self._embedding_provider = value.strip().lower()

    @property
    def embedding_model_name(self) -> str:
        return self._embedding_model_name

    @embedding_model_name.setter
    def embedding_model_name(self, value: str):
        self._embedding_model_name = value.strip()

    @property
    def vector_db_dir(self) -> str:
        return self._vector_db_dir

    @vector_db_dir.setter
    def vector_db_dir(self, value: str):
        self._vector_db_dir = value

    @property
    def log_level(self) -> str:
        return self._log_level

    @log_level.setter
    def log_level(self, value: str):
        self._log_level = value.upper()


# Shared configurations singleton
settings = Settings()
