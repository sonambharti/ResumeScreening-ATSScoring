from langchain_core.embeddings import Embeddings
from resume_ats_agent.config.settings import settings
from resume_ats_agent.core.exceptions import EmbeddingError
from resume_ats_agent.core.logger import logger

class EmbeddingServiceFactory:
    """Factory Class to instantiate the appropriate LangChain Embeddings provider."""
    
    @staticmethod
    def get_embeddings() -> Embeddings:
        """Create and return an Embeddings instance based on active settings.
        
        Returns:
            Embeddings: A LangChain Embeddings interface implementation.
            
        Raises:
            EmbeddingError: If API keys are missing or provider is unsupported.
        """
        provider = settings.embedding_provider
        model_name = settings.embedding_model_name
        
        logger.info(f"Initializing embeddings. Provider: '{provider}', Model: '{model_name}'")
        
        if provider == "openai":
            if not settings.openai_api_key:
                raise EmbeddingError(
                    "OpenAI API key is missing. Please configure it in your Settings/UI or .env file."
                )
            try:
                from langchain_openai import OpenAIEmbeddings
                return OpenAIEmbeddings(model=model_name, api_key=settings.openai_api_key)
            except Exception as e:
                raise EmbeddingError(f"Failed to initialize OpenAI Embeddings: {str(e)}")
                
        elif provider in ["gemini", "google"]:
            if not settings.gemini_api_key:
                raise EmbeddingError(
                    "Gemini API key is missing. Please configure it in your Settings/UI or .env file."
                )
            try:
                from langchain_google_genai import GoogleGenAIEmbeddings
                # Note: Default model is typically 'models/embedding-001'
                return GoogleGenAIEmbeddings(model=model_name, google_api_key=settings.gemini_api_key)
            except Exception as e:
                raise EmbeddingError(f"Failed to initialize Gemini Embeddings: {str(e)}")
                
        elif provider == "huggingface":
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                logger.info("Initializing HuggingFace local embeddings (requires 'sentence-transformers').")
                return HuggingFaceEmbeddings(model_name=model_name)
            except Exception as e:
                raise EmbeddingError(
                    f"Failed to initialize local HuggingFace embeddings. "
                    f"Make sure 'sentence-transformers' is installed. Error: {str(e)}"
                )
        else:
            raise EmbeddingError(
                f"Unsupported embedding provider '{provider}'. "
                f"Use 'openai', 'gemini', or 'huggingface'."
            )
