from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class ContactInfo(BaseModel):
    name: Optional[str] = Field(None, description="Candidate's full name.")
    email: Optional[str] = Field(None, description="Candidate's email address.")
    phone: Optional[str] = Field(None, description="Candidate's phone number.")
    links: List[str] = Field(default_factory=list, description="Links to portfolios or profiles like LinkedIn, GitHub, websites.")

class WorkExperience(BaseModel):
    job_title: str = Field(..., description="Role title, e.g., Senior Software Engineer.")
    company: str = Field(..., description="Name of the company.")
    date_range: Optional[str] = Field(None, description="Dates worked, e.g., Jan 2020 - Present.")
    responsibilities: List[str] = Field(default_factory=list, description="Key duties and achievements performed.")
    duration_years: Optional[float] = Field(None, description="Approximate duration of work in years.")

class Education(BaseModel):
    degree: str = Field(..., description="Degree earned, e.g., Bachelor of Science.")
    major: str = Field(..., description="Field of study, e.g., Computer Science.")
    institution: str = Field(..., description="University, College, or School name.")
    graduation_year: Optional[str] = Field(None, description="Year of graduation.")
    gpa: Optional[str] = Field(None, description="Reported GPA if mentioned.")

class ParsedResume(BaseModel):
    filename: str = Field(..., description="Source filename of the resume.")
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    skills: List[str] = Field(default_factory=list, description="List of technical and soft skills parsed.")
    experience: List[WorkExperience] = Field(default_factory=list, description="List of professional job experiences.")
    education: List[Education] = Field(default_factory=list, description="List of educational backgrounds.")
    certifications: List[str] = Field(default_factory=list, description="Licenses, certifications, or courses.")
    raw_text: str = Field(..., description="Raw text content extracted from the file.")

class ATSScoreBreakdown(BaseModel):
    skills_score: float = Field(..., ge=0, le=100, description="Score based on technical and soft skills match (0-100).")
    experience_score: float = Field(..., ge=0, le=100, description="Score based on job roles, experience length, and relevance (0-100).")
    education_score: float = Field(..., ge=0, le=100, description="Score based on degree and study field relevance (0-100).")
    certifications_score: float = Field(..., ge=0, le=100, description="Score based on certifications relevance (0-100).")

class SkillMatchDetail(BaseModel):
    matching_skills: List[str] = Field(default_factory=list, description="Skills listed in the resume that match the job description.")
    missing_skills: List[str] = Field(default_factory=list, description="Critical skills in the job description that are missing or weak in the resume.")
    unrealized_strengths: List[str] = Field(default_factory=list, description="Skills in the resume that are highly relevant but not explicitly listed in the job description.")

class ATSScoringReport(BaseModel):
    candidate_name: str = Field(..., description="Name of the candidate being scored.")
    overall_score: float = Field(..., ge=0, le=100, description="Overall weighted ATS score (0-100).")
    breakdown: ATSScoreBreakdown = Field(..., description="Category-wise score details.")
    skill_matching: SkillMatchDetail = Field(..., description="Matching and missing skills detail.")
    experience_verdict: str = Field(..., description="AI evaluation of the candidate's professional experience.")
    improvement_feedback: List[str] = Field(default_factory=list, description="Actionable bullet-point suggestions to improve the resume for this JD.")
    verdict: str = Field(..., description="Overall screening verdict (e.g., Strongly Recommend, Recommend, Interview, Reject).")
