import os
from typing import Dict, List, Any, Tuple
from resume_ats_agent.config.settings import settings
from resume_ats_agent.core.logger import logger
from resume_ats_agent.core.exceptions import ParserError, ScoringError
from resume_ats_agent.models.schemas import ParsedResume, ATSScoringReport
from resume_ats_agent.parsers.factory import ResumeParserFactory
from resume_ats_agent.rag.vector_store import VectorStoreManager
from resume_ats_agent.engine.scoring import ScoringEngine
from resume_ats_agent.agents.ats_agent import ATSAgentManager

class ScreeningSystemFacade:
    """Facade Pattern to simplify interaction with the parsing, scoring, RAG, and agent subsystems."""
    
    def __init__(self):
        self.vector_store = VectorStoreManager()
        self.scoring_engine = ScoringEngine()
        
        # Local state cache
        self.parsed_resumes: Dict[str, ParsedResume] = {}
        self.active_jd: str = ""
        
        # Initialize Agent Manager passing closures to bind with facade state
        self.agent_manager = ATSAgentManager(
            vector_store=self.vector_store,
            scoring_engine=self.scoring_engine,
            get_candidate_cache=lambda: self.parsed_resumes,
            get_active_jd=lambda: self.active_jd
        )
        
    def set_job_description(self, jd: str):
        """Set the active system Job Description."""
        self.active_jd = jd.strip()
        logger.info(f"Active Job Description updated (length: {len(self.active_jd)} characters).")

    def upload_and_process_resume(self, file_path: str) -> ParsedResume:
        """Parse a resume file, extract structured info using LLM, cache, and index in RAG vector store."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Resume file not found at: {file_path}")
            
        filename = os.path.basename(file_path)
        logger.info(f"Facade: Processing file upload '{filename}'")
        
        try:
            # 1. Choose parser and extract raw text
            parser = ResumeParserFactory.get_parser(file_path)
            raw_text = parser.parse(file_path)
            
            # 2. Extract structured fields from raw text via LLM
            parsed_resume = self.scoring_engine.parse_resume_text(raw_text, filename)
            
            # 3. Cache the parsed object
            self.parsed_resumes[filename] = parsed_resume
            
            # 4. Chunk and Index in the RAG Vector Store
            resume_record = {
                "filename": filename,
                "candidate_name": parsed_resume.contact_info.name or filename,
                "raw_text": raw_text
            }
            self.vector_store.add_resumes([resume_record])
            
            return parsed_resume
            
        except Exception as e:
            logger.error(f"Error processing upload '{filename}': {str(e)}")
            raise ParserError(f"Failed to upload and parse '{filename}': {str(e)}")

    def score_single_resume(self, filename: str, weights: Dict[str, float] = None) -> ATSScoringReport:
        """Evaluate a specific uploaded resume against the active Job Description."""
        if filename not in self.parsed_resumes:
            raise KeyError(f"Candidate file '{filename}' has not been uploaded or processed.")
            
        if not self.active_jd.strip():
            raise ScoringError("Please set a Job Description first before scoring.")
            
        resume = self.parsed_resumes[filename]
        return self.scoring_engine.score_resume(resume, self.active_jd, weights)

    def screen_all_candidates(self, weights: Dict[str, float] = None) -> List[ATSScoringReport]:
        """Evaluate all parsed resumes in the cache against the active JD, returning a ranked leaderboard."""
        if not self.parsed_resumes:
            return []
            
        if not self.active_jd.strip():
            raise ScoringError("Please set a Job Description first before running screening.")
            
        reports = []
        for filename in self.parsed_resumes.keys():
            try:
                report = self.score_single_resume(filename, weights)
                reports.append(report)
            except Exception as e:
                logger.error(f"Failed to score '{filename}' in batch screening: {str(e)}")
                
        # Sort leaderboard by overall score descending
        reports.sort(key=lambda r: r.overall_score, reverse=True)
        return reports

    def search_candidates_rag(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic RAG search across resumes, returning candidate metadata and excerpt matches."""
        results = self.vector_store.search(query, k=k)
        formatted = []
        for doc, score in results:
            formatted.append({
                "candidate_name": doc.metadata.get("candidate_name", "Unknown"),
                "filename": doc.metadata.get("filename", "Unknown"),
                "excerpt": doc.page_content,
                # Score is L2 distance in FAISS (closer to 0 is better). Convert to a mock similarity %
                "relevance_score": round(max(0, 100 - (score * 50)), 1) 
            })
        return formatted

    def chat_with_recruiter_agent(self, user_message: str, chat_history: List[Any]) -> str:
        """Run the ReAct agent to answer recruitment queries, passing along context and history."""
        history_str = ""
        # Support both legacy list of tuples/lists and modern list of dicts/ChatMessages
        for msg in chat_history[-5:]:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_str += f"User: {content}\n" if role == "user" else f"Agent: {content}\n"
            elif isinstance(msg, (list, tuple)) and len(msg) == 2:
                user_m, bot_m = msg
                history_str += f"User: {user_m}\nAgent: {bot_m}\n"
            else:
                # Fallback to duck-typing for objects with role/content properties (like gr.ChatMessage)
                role = getattr(msg, "role", "user")
                content = getattr(msg, "content", "")
                history_str += f"User: {content}\n" if role == "user" else f"Agent: {content}\n"
            
        return self.agent_manager.run_agent(user_message, history_str)

    def clear_database(self):
        """Clears all cached resumes, vector store indexing files, and resets the ReAct agent."""
        self.parsed_resumes.clear()
        self.vector_store.clear()
        self.agent_manager.reset_agent()
        logger.info("ScreeningSystemFacade: Database cleared completely.")
        
    def reset_agent(self):
        """Resets agent executor (e.g. if API keys are modified)."""
        self.agent_manager.reset_agent()
