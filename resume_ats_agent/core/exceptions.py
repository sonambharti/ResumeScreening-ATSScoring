class ResumeATSError(Exception):
    """Base exception for all Resume Screening and ATS Scoring platform errors."""
    pass

class ConfigurationError(ResumeATSError):
    """Raised when configuration values are missing, invalid, or API keys are not supplied."""
    pass

class ParserError(ResumeATSError):
    """Raised when there is an issue reading or extracting text from a resume file."""
    pass

class EmbeddingError(ResumeATSError):
    """Raised when there is a failure generating embeddings for texts."""
    pass

class VectorStoreError(ResumeATSError):
    """Raised when vector store indexing, retrieval, or loading fails."""
    pass

class ScoringError(ResumeATSError):
    """Raised during the ATS scoring computation or model analysis phase."""
    pass

class AgentExecutionError(ResumeATSError):
    """Raised when the LangChain ReAct agent execution encounters a failure."""
    pass
