import os
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from resume_ats_agent.config.settings import settings
from resume_ats_agent.models.schemas import (
    ParsedResume, ATSScoringReport, ATSScoreBreakdown, SkillMatchDetail,
    ContactInfo, WorkExperience, Education
)
from resume_ats_agent.core.exceptions import ScoringError, ConfigurationError
from resume_ats_agent.core.logger import logger

class ResumeDataStructure(BaseModel):
    """Auxiliary Pydantic schema used for structured LLM parsing of raw resumes."""
    contact_info: ContactInfo = Field(default_factory=ContactInfo, description="Candidate name, email, phone, and links.")
    skills: List[str] = Field(default_factory=list, description="Extracted technical and soft skills.")
    experience: List[WorkExperience] = Field(default_factory=list, description="Extracted work history.")
    education: List[Education] = Field(default_factory=list, description="Extracted educational background.")
    certifications: List[str] = Field(default_factory=list, description="Extracted licenses and certifications.")

class ATSScoringRawOutput(BaseModel):
    """Auxiliary Pydantic schema used for structured LLM evaluations of candidate fit."""
    skills_score: float = Field(..., description="Score 0-100 based on technical and soft skills match.")
    experience_score: float = Field(..., description="Score 0-100 based on roles, experience duration, and responsibilities.")
    education_score: float = Field(..., description="Score 0-100 based on degree, major, and school alignment.")
    certifications_score: float = Field(..., description="Score 0-100 based on relevance of credentials and courses.")
    matching_skills: List[str] = Field(..., description="Skills from resume that match the job description.")
    missing_skills: List[str] = Field(..., description="Required/preferred JD skills missing or weak in the resume.")
    unrealized_strengths: List[str] = Field(..., description="Skills in resume that are highly relevant but not explicitly demanded.")
    experience_verdict: str = Field(..., description="Brief summary evaluation of the candidate's professional experience fit.")
    improvement_feedback: List[str] = Field(..., description="Actionable suggestions to improve the resume for this specific JD.")
    verdict: str = Field(..., description="Overall screening verdict (Strongly Recommend, Recommend, Interview, or Reject).")

class ScoringEngine:
    """Handles structured resume parsing and ATS matching evaluations using LLMs."""
    
    def __init__(self):
        pass
        
    def _get_llm(self, temperature: float = 0.0):
        provider = settings.default_llm_provider
        model_name = settings.default_model_name
        
        logger.info(f"ScoringEngine: Initializing LLM '{model_name}' from provider '{provider}'")
        
        if provider == "openai":
            if not settings.openai_api_key:
                raise ConfigurationError(
                    "OpenAI API key is missing. Please configure it in your Settings/UI or .env file."
                )
            try:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(model=model_name, temperature=temperature, api_key=settings.openai_api_key)
            except Exception as e:
                raise ConfigurationError(f"Failed to initialize ChatOpenAI: {str(e)}")
                
        elif provider in ["gemini", "google"]:
            if not settings.gemini_api_key:
                raise ConfigurationError(
                    "Gemini API key is missing. Please configure it in your Settings/UI or .env file."
                )
            try:
                from langchain_google_genai import ChatGoogleGenAI
                return ChatGoogleGenAI(model=model_name, temperature=temperature, google_api_key=settings.gemini_api_key)
            except Exception as e:
                raise ConfigurationError(f"Failed to initialize ChatGoogleGenAI: {str(e)}")
                
        elif provider == "groq":
            if not settings.groq_api_key:
                raise ConfigurationError(
                    "Groq API key is missing. Please configure it in your Settings/UI or .env file."
                )
            try:
                from langchain_groq import ChatGroq
                return ChatGroq(model_name=model_name, temperature=temperature, api_key=settings.groq_api_key)
            except Exception as e:
                raise ConfigurationError(f"Failed to initialize ChatGroq: {str(e)}")
                
        else:
            raise ConfigurationError(
                f"Unsupported LLM provider '{provider}'. Choose 'openai', 'gemini', or 'groq'."
            )


    def parse_resume_text(self, raw_text: str, filename: str) -> ParsedResume:
        """Parse raw resume text into a structured Pydantic model using LLM structured output.
        
        Args:
            raw_text (str): Raw string content extracted from the resume.
            filename (str): The filename of the resume.
            
        Returns:
            ParsedResume: Structured candidate data.
        """
        if not raw_text.strip():
            raise ScoringError("Cannot parse empty resume content.")
            
        try:
            llm = self._get_llm(temperature=0.0)
            structured_llm = llm.with_structured_output(ResumeDataStructure)
            
            prompt = (
                "You are an expert CV and Resume parsing engine. Carefully extract "
                "the contact info, skills, work experience, education history, and "
                "certifications from the raw text provided below. Be precise and comprehensive.\n\n"
                f"--- RESUME RAW TEXT ---\n{raw_text}\n"
            )
            
            extracted_data = structured_llm.invoke(prompt)
            
            return ParsedResume(
                filename=filename,
                contact_info=extracted_data.contact_info,
                skills=extracted_data.skills,
                experience=extracted_data.experience,
                education=extracted_data.education,
                certifications=extracted_data.certifications,
                raw_text=raw_text
            )
        except Exception as e:
            logger.error(f"Error during LLM resume parsing: {str(e)}")
            # Fallback to an empty structured model to avoid crashing the pipeline
            logger.info("Falling back to generic empty structured model.")
            candidate_name = os.path.splitext(os.path.basename(filename))[0]
            return ParsedResume(
                filename=filename,
                contact_info=ContactInfo(name=candidate_name),
                skills=[],
                experience=[],
                education=[],
                certifications=[],
                raw_text=raw_text
            )

    def score_resume(self, resume: ParsedResume, job_description: str, weights: Dict[str, float] = None) -> ATSScoringReport:
        """Audit and match candidate details against a job description, computing a weighted overall score.
        
        Args:
            resume (ParsedResume): The structured candidate resume.
            job_description (str): Text requirements of the job description.
            weights (Dict[str, float]): Scoring weights. If None, default system settings will be used.
            
        Returns:
            ATSScoringReport: Full comparative feedback, category breakdown, and matching metrics.
        """
        if not job_description.strip():
            raise ScoringError("Cannot run ATS matching against an empty job description.")
            
        if not weights:
            weights = settings.default_weights
            
        # Normalize weights so they sum to 1.0
        total_weight = sum(weights.values())
        if total_weight == 0:
            weights = {"skills": 0.4, "experience": 0.35, "education": 0.15, "certifications": 0.1}
            total_weight = 1.0
        normalized_weights = {k: v / total_weight for k, v in weights.items()}
        
        try:
            llm = self._get_llm(temperature=0.0)
            structured_llm = llm.with_structured_output(ATSScoringRawOutput)
            
            # Format candidate resume metadata for the prompt
            candidate_details = (
                f"Candidate Name: {resume.contact_info.name or 'Not specified'}\n"
                f"Skills: {', '.join(resume.skills) if resume.skills else 'None extracted'}\n\n"
                "Work Experience:\n"
            )
            for exp in resume.experience:
                candidate_details += f"- Job Title: {exp.job_title} at {exp.company} ({exp.date_range or 'N/A'})\n"
                if exp.responsibilities:
                    candidate_details += "  Responsibilities:\n"
                    for resp in exp.responsibilities:
                        candidate_details += f"    * {resp}\n"
                        
            candidate_details += "\nEducation:\n"
            for edu in resume.education:
                candidate_details += f"- {edu.degree} in {edu.major} from {edu.institution} (Graduation: {edu.graduation_year or 'N/A'})\n"
                
            candidate_details += f"\nCertifications: {', '.join(resume.certifications) if resume.certifications else 'None extracted'}"
            
            prompt = (
                "You are an elite Recruiter and ATS Auditor. Review the Candidate Profile below and match it "
                "against the requirements in the Job Description. Assign scores from 0 to 100 for each section "
                "(skills, experience, education, certifications). Be objective and realistic (do not overscore "
                "poor alignment or underscore strong fit).\n\n"
                f"=== JOB DESCRIPTION ===\n{job_description}\n\n"
                f"=== CANDIDATE PROFILE ===\n{candidate_details}\n"
            )
            
            raw_report = structured_llm.invoke(prompt)
            
            # Mathematically compute the overall score based on category weights
            overall_score = (
                raw_report.skills_score * normalized_weights.get("skills", 0.4) +
                raw_report.experience_score * normalized_weights.get("experience", 0.35) +
                raw_report.education_score * normalized_weights.get("education", 0.15) +
                raw_report.certifications_score * normalized_weights.get("certifications", 0.1)
            )
            overall_score = round(overall_score, 1)
            
            return ATSScoringReport(
                candidate_name=resume.contact_info.name or os.path.splitext(os.path.basename(resume.filename))[0],
                overall_score=overall_score,
                breakdown=ATSScoreBreakdown(
                    skills_score=raw_report.skills_score,
                    experience_score=raw_report.experience_score,
                    education_score=raw_report.education_score,
                    certifications_score=raw_report.certifications_score
                ),
                skill_matching=SkillMatchDetail(
                    matching_skills=raw_report.matching_skills,
                    missing_skills=raw_report.missing_skills,
                    unrealized_strengths=raw_report.unrealized_strengths
                ),
                experience_verdict=raw_report.experience_verdict,
                improvement_feedback=raw_report.improvement_feedback,
                verdict=raw_report.verdict
            )
        except Exception as e:
            logger.error(f"Error during ATS evaluation: {str(e)}")
            raise ScoringError(f"Failed to score resume against Job Description: {str(e)}")
