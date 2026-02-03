"""
Sample Resume and JobDescription instances for testing the graph workflow.

Use these when parsing is not yet implemented: build initial state with
sample_resume() and sample_job_description(), then invoke the graph.
"""
from datetime import datetime

from schemas.personal_info import PersonalInfo
from schemas.resume import Resume
from schemas.education import Education
from schemas.experience import Experience
from schemas.skill import Skill
from schemas.certification import Certification
from schemas.language import Language
from schemas.project import Project
from schemas.job_description import JobDescription
from enums import SkillType, LanguageProficiencyLevel


def sample_resume() -> Resume:
    """
    Return a minimal but valid Resume aligned with a Python/backend profile.
    Overlaps with sample_job_description() so mapping can yield a decent score.
    """
    personal_info = PersonalInfo(
        full_name="Jane Doe",
        phone_number="+1 555 123 4567",
        email_address="jane.doe@example.com",
        linkedin="https://linkedin.com/in/janedoe",
        personal_website=None,
    )

    educations = [
        Education(
            degree="B.S.",
            major="Computer Science",
            university_name="State University",
            city="Boston",
            country="USA",
            start_date=datetime(2018, 9, 1),
            end_date=datetime(2022, 6, 1),
        ),
    ]

    experiences = [
        Experience(
            role_title="Junior Backend Developer",
            company_name="Tech Corp",
            start_date=datetime(2022, 7, 1),
            end_date=datetime(2024, 12, 1),
            description=[
                "Developed REST APIs in Python and maintained PostgreSQL databases.",
                "Collaborated with frontend team on integration and error handling.",
            ],
            is_volunteer=False,
        ),
    ]

    skills = [
        Skill(skill_name="Python", skill_type=SkillType.TECHNICAL),
        Skill(skill_name="SQL", skill_type=SkillType.TECHNICAL),
        Skill(skill_name="REST APIs", skill_type=SkillType.TECHNICAL),
        Skill(skill_name="Teamwork", skill_type=SkillType.SOFT),
    ]

    certifications = [
        Certification(
            certification_name="AWS Cloud Practitioner",
            issuing_organization="Amazon Web Services",
            issue_date=datetime(2023, 3, 15),
        ),
    ]

    languages = [
        Language(language="English", proficiency_level=LanguageProficiencyLevel.C1),
    ]

    projects = [
        Project(
            project_name="Inventory API",
            description=[
                "REST API for inventory management using FastAPI and SQLAlchemy.",
            ],
            project_link="https://github.com/janedoe/inventory-api",
        ),
    ]

    return Resume(
        personal_info=personal_info,
        summary="Computer Science graduate with 2+ years of backend development experience in Python and SQL. Focused on APIs and database design.",
        educations=educations,
        experiences=experiences,
        skills=skills,
        certifications=certifications,
        languages=languages,
        projects=projects,
    )


def sample_job_description() -> JobDescription:
    """
    Return a JobDescription that partially matches sample_resume()
    (Python, backend, APIs) so the mapping node can produce matches and gaps.
    """
    return JobDescription(
        job_title="Backend Developer",
        company_name="Acme Inc.",
        responsibilities=[
            "Design and implement REST APIs and microservices.",
            "Maintain and optimize PostgreSQL and caching layers.",
            "Work with frontend and product teams on requirements.",
        ],
        requirements=[
            "Bachelor's degree in Computer Science or equivalent.",
            "2+ years of experience in backend development.",
            "Strong experience with Python and relational databases.",
        ],
        required_skills=["Python", "SQL", "REST APIs", "PostgreSQL"],
        preferred_skills=["FastAPI", "Django", "Docker", "AWS"],
        seniority_level="mid",
        soft_skills=["communication", "teamwork", "problem solving"],
    )
