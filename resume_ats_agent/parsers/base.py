from abc import ABC, abstractmethod

class BaseResumeParser(ABC):
    """Abstract Base Class defining the Strategy interface for Resume Parsers."""
    
    @abstractmethod
    def parse(self, file_path: str) -> str:
        """Parse resume file and extract raw text.
        
        Args:
            file_path (str): The absolute path to the file.
            
        Returns:
            str: Extracted text content.
            
        Raises:
            ParserError: If parsing fails.
        """
        pass
