def job_text_to_json_prompt(job_text: str) -> str:
    return f"""
You are an AI that extracts structured job description data.

STRICT RULES:
- Output ONLY valid JSON
- No explanations
- All lists must be arrays of strings
- Match this schema exactly
- IMPORTANT: Keep the output in the SAME language as the input text
- Extract ALL responsibilities and ALL requirements mentioned.
- Do not omit items.
- required_skills: ONLY tools, technologies, or measurable hard skills
- Do NOT include responsibilities as skills
- Do NOT put vague traits like "ownership", "AI mindset", or "proactive" in
  required_skills; these belong in responsibilities, requirements, or
  soft_skills instead.
- If seniority not mentioned, set "mid"
- Junior if internship/entry-level
- Senior if 5+ years or manager role
- If a section is missing, return an empty list []
- Return null if the company name is not explicitly written.
- Do NOT guess or infer company names.




Schema:

JobDescription {{
  job_title: str,
  company_name: str | null,

  responsibilities: [str],
  requirements: [str],

  required_skills: [str],
  preferred_skills: [str],

  seniority_level: "junior" | "mid" | "senior" | "lead",

  soft_skills: [str]
}}

Instructions:

- responsibilities: tasks and duties
- requirements: education, experience, qualifications
- required_skills: must-have technical skills
- preferred_skills: nice-to-have skills
- soft_skills: teamwork, communication, etc.
- seniority_level must be one of:
  junior / mid / senior / lead

Job text:
{job_text}
"""
