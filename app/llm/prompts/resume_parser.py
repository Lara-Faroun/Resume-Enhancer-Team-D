def resume_text_to_json_prompt(resume_text: str) -> str:
    return f"""
You are an AI resume parser.

Your task is to extract resume information and return ONLY valid JSON.

STRICT RULES:
- Output ONLY JSON (no explanations).
- Keys MUST match the schema exactly.
- Dates MUST be ISO format: YYYY-MM-DD
- If an end_date is "Present", return null.
- Skills MUST include skill_type: technical or soft.
- Languages MUST include proficiency_level: A1, A2, B1, B2, C1, C2.

--------------------------------------------------

Schema (must match exactly):

{{
  "personal_info": {{
    "full_name": "string",
    "phone_number": "string",
    "email_address": "string",
    "linkedin": "string or null",
    "personal_website": "string or null"
  }},

  "summary": "string",

  "educations": [
    {{
      "degree": "string",
      "major": "string",
      "university_name": "string",
      "city": "string",
      "country": "string",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD or null"
    }}
  ],

  "experiences": [
    {{
      "role_title": "string",
      "company_name": "string",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD or null",
      "description": ["string"],
      "is_volunteer": false
    }}
  ],

  "skills": [
    {{
      "skill_name": "string",
      "skill_type": "technical or soft"
    }}
  ],

  "certifications": [
    {{
      "certification_name": "string",
      "issuing_organization": "string",
      "issue_date": "YYYY-MM-DD or null"
    }}
  ],

  "languages": [
    {{
      "language": "string",
      "proficiency_level": "A1|A2|B1|B2|C1|C2|Native"
    }}
  ],

  "projects": [
    {{
      "project_name": "string",
      "description": ["string"],
      "project_link": "string or null"
    }}
  ]
}}

--------------------------------------------------

Resume text:
{resume_text}
"""
