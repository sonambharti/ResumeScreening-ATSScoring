import os
from resume_ats_agent.parsers.base import BaseResumeParser
from resume_ats_agent.core.exceptions import ParserError
from resume_ats_agent.core.logger import logger

class PDFParser(BaseResumeParser):
    """Concrete parser strategy to extract text content from PDF resume files."""
    
    def parse(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise ParserError(f"File not found: {file_path}")
            
        logger.info(f"Parsing PDF file: {file_path}")
        text = ""
        
        # Attempt primary parsing using pdfplumber (superior layout parsing)
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if text.strip():
                logger.info("PDF parsed successfully using pdfplumber.")
                return text
        except ImportError:
            logger.warning("pdfplumber not imported. Attempting fallback.")
        except Exception as e:
            logger.warning(f"pdfplumber failed: {str(e)}. Attempting fallback.")
            
        # Fallback to standard pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            if text.strip():
                logger.info("PDF parsed successfully using pypdf fallback.")
                return text
        except Exception as e:
            raise ParserError(f"Failed to parse PDF file '{file_path}': {str(e)}")
            
        raise ParserError(f"No textual content could be extracted from PDF file: {file_path}")
