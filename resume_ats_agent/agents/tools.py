from langchain_core.tools import tool
from typing import Dict, List, Any, Callable
from resume_ats_agent.models.schemas import ParsedResume
from resume_ats_agent.rag.vector_store import VectorStoreManager
from resume_ats_agent.engine.scoring import ScoringEngine
from resume_ats_agent.core.logger import logger

def create_screening_tools(
    vector_store: VectorStoreManager,
    scoring_engine: ScoringEngine,
    get_candidate_cache: Callable[[], Dict[str, ParsedResume]],
    get_active_jd: Callable[[], str]
) -> List[Any]:
    """Factory function to build LangChain tools bound to current system components.
    
    Args:
        vector_store: VectorStoreManager instance.
        scoring_engine: ScoringEngine instance.
        get_candidate_cache: Callable returning the dictionary of parsed resumes.
        get_active_jd: Callable returning the current active Job Description string.
        
    Returns:
        List: List of LangChain Tool objects.
    """
    
    @tool
    def list_candidates(dummy: str = "") -> str:
        """List all candidates currently uploaded and indexed in the system. Use this to see who is available."""
        cache = get_candidate_cache()
        if not cache:
            return "No candidates are currently uploaded in the system."
        
        names = []
        for fn, resume in cache.items():
            name = resume.contact_info.name or fn
            names.append(f"- {name} (Source file: {fn})")
        return "Available Candidates in Database:\n" + "\n".join(names)

    @tool
    def get_candidate_details(candidate_identifier: str) -> str:
        """Retrieve detailed parsed resume data (skills, experience, education, certifications) for a specific candidate.
        
        Args:
            candidate_identifier: The name of the candidate or their resume filename.
        """
        cache = get_candidate_cache()
        if not cache:
            return "No candidates are currently uploaded in the system."
            
        target_resume = None
        ident = candidate_identifier.lower().strip()
        
        # Try finding a matching candidate in the cache
        for fn, resume in cache.items():
            name = (resume.contact_info.name or "").lower().strip()
            filename = fn.lower().strip()
            if ident in name or ident in filename or name in ident or filename in ident:
                target_resume = resume
                break
                
        if not target_resume:
            return (
                f"Candidate '{candidate_identifier}' not found. "
                "Use 'list_candidates' to see the exact names of uploaded profiles."
            )
            
        # Format the resume details in a highly readable format for the agent
        res = f"=== PROFILE DETAILS FOR: {target_resume.contact_info.name or 'Not Specified'} ===\n"
        res += f"File: {target_resume.filename}\n"
        res += f"Email: {target_resume.contact_info.email or 'N/A'}\n"
        res += f"Phone: {target_resume.contact_info.phone or 'N/A'}\n"
        res += f"Links: {', '.join(target_resume.contact_info.links) if target_resume.contact_info.links else 'None'}\n"
        res += f"Skills: {', '.join(target_resume.skills) if target_resume.skills else 'None'}\n\n"
        
        res += "Professional Experience:\n"
        if target_resume.experience:
            for i, exp in enumerate(target_resume.experience, 1):
                res += f"{i}. {exp.job_title} at {exp.company} ({exp.date_range or 'Dates not specified'})\n"
                for resp in exp.responsibilities:
                    res += f"   * {resp}\n"
        else:
            res += "  No experience details extracted.\n"
                
        res += "\nEducation Details:\n"
        if target_resume.education:
            for i, edu in enumerate(target_resume.education, 1):
                res += f"{i}. {edu.degree} in {edu.major} from {edu.institution} (Class of {edu.graduation_year or 'N/A'}, GPA: {edu.gpa or 'N/A'})\n"
        else:
            res += "  No education details extracted.\n"
            
        res += f"\nCertifications: {', '.join(target_resume.certifications) if target_resume.certifications else 'None'}\n"
        return res

    @tool
    def search_resumes_rag(query: str) -> str:
        """Search across all uploaded resumes using semantic search (RAG) to find specific skills, experiences, or details.
        
        Args:
            query: The search query, e.g., 'experience with Kubernetes' or 'React developer'.
        """
        try:
            results = vector_store.search(query, k=5)
            if not results:
                return f"No matching resume content found for search query: '{query}'"
                
            formatted = []
            for doc, score in results:
                name = doc.metadata.get("candidate_name", "Unknown")
                file = doc.metadata.get("filename", "Unknown")
                # Representing matching text block. Score is L2 distance, lower is closer.
                formatted.append(
                    f"Candidate: {name} (File: {file})\n"
                    f"Matching Passage: ... {doc.page_content.strip()} ...\n"
                    f"---"
                )
            return f"Semantic RAG Search Results for '{query}':\n\n" + "\n\n".join(formatted)
        except Exception as e:
            return f"Failed to execute semantic search: {str(e)}"

    @tool
    def evaluate_candidate_fit(candidate_identifier: str) -> str:
        """Evaluate how well a specific candidate matches the active Job Description. Computes and returns the ATS Scoring Report.
        
        Args:
            candidate_identifier: The name of the candidate or their resume filename.
        """
        cache = get_candidate_cache()
        jd = get_active_jd()
        
        if not cache:
            return "No candidates are currently uploaded in the system."
        if not jd.strip():
            return "No active Job Description is configured. Please paste a Job Description first."
            
        target_resume = None
        ident = candidate_identifier.lower().strip()
        
        # Match name or filename
        for fn, resume in cache.items():
            name = (resume.contact_info.name or "").lower().strip()
            filename = fn.lower().strip()
            if ident in name or ident in filename or name in ident or filename in ident:
                target_resume = resume
                break
                
        if not target_resume:
            return (
                f"Candidate '{candidate_identifier}' not found. "
                "Use 'list_candidates' to find matching profiles."
            )
            
        try:
            report = scoring_engine.score_resume(target_resume, jd)
            
            res = f"=== ATS MATCH REPORT FOR {report.candidate_name.upper()} ===\n"
            res += f"OVERALL ATS SCORE: {report.overall_score}/100\n"
            res += f"VERDICT: {report.verdict}\n\n"
            res += "BREAKDOWN:\n"
            res += f"- Skills Alignment: {report.breakdown.skills_score}/100\n"
            res += f"- Experience Relevance: {report.breakdown.experience_score}/100\n"
            res += f"- Education Match: {report.breakdown.education_score}/100\n"
            res += f"- Certifications Match: {report.breakdown.certifications_score}/100\n\n"
            
            res += "SKILL ANALYSIS:\n"
            res += f"- Matching: {', '.join(report.skill_matching.matching_skills) if report.skill_matching.matching_skills else 'None'}\n"
            res += f"- Missing: {', '.join(report.skill_matching.missing_skills) if report.skill_matching.missing_skills else 'None'}\n"
            res += f"- Strengths/Extras: {', '.join(report.skill_matching.unrealized_strengths) if report.skill_matching.unrealized_strengths else 'None'}\n\n"
            
            res += f"EXPERIENCE VERDICT:\n{report.experience_verdict}\n\n"
            res += "IMPROVEMENT SUGGESTIONS:\n"
            for feedback in report.improvement_feedback:
                res += f"- {feedback}\n"
            return res
        except Exception as e:
            return f"Failed to compute scoring evaluation: {str(e)}"

    return [list_candidates, get_candidate_details, search_resumes_rag, evaluate_candidate_fit]
