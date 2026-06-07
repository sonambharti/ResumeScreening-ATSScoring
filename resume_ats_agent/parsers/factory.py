import os
from resume_ats_agent.parsers.base import BaseResumeParser
from resume_ats_agent.parsers.pdf_parser import PDFParser
from resume_ats_agent.parsers.docx_parser import DocxParser
from resume_ats_agent.core.exceptions import ParserError

class ResumeParserFactory:
    """Factory Class (Factory Pattern) to generate the appropriate ResumeParser instance."""
    
    @staticmethod
    def get_parser(file_path: str) -> BaseResumeParser:
        """Return the appropriate parser strategy based on the file extension.
        
        Args:
            file_path (str): Path to the resume file.
            
        Returns:
            BaseResumeParser: An instantiated concrete parser strategy.
            
        Raises:
            ParserError: If the file format is unsupported.
        """
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == ".pdf":
            return PDFParser()
        elif ext in [".docx", ".doc"]:
            # Note: docx parser handles both, older .doc files will raise error at library level 
            # if they aren't standard XML. This is standard behavior.
            return DocxParser()
        else:
            raise ParserError(
                f"Unsupported file extension '{ext}'. Only .pdf and .docx (.doc) files are supported."
            )
