from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class SkillTaxonomy(BaseModel):
    languages: List[str] = []
    frameworks: List[str] = []
    databases: List[str] = []
    ml_ai_tools: List[str] = []
    cloud_devops: List[str] = []
    core_concepts: List[str] = []


class ResumeParseResult(BaseModel):
    candidate_name: Optional[str] = "Candidate"
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: SkillTaxonomy
    raw_skills_list: List[str] = []
    domains_detected: List[str] = []
    projects_detected: List[str] = []
    experience_level_inferred: str = "Junior / Mid"
    total_characters_parsed: int
    matched_role_alignment: float = 0.0  # 0.0 to 1.0
