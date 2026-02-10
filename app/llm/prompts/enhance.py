"""Prompts for enhancing resume sections against a mapping (no JD needed here)."""

ENHANCE_SYSTEM = """You are an expert resume writer helping a candidate tailor
their resume to a specific job description.

Your task is to enhance the existing resume sections while strictly following
these rules:

- Do NOT invent or fabricate experience, skills, certifications, projects, or organizations.
- Do NOT add technologies that are not present in the original resume.
- Do NOT change factual quantities unless the original resume is clearly inconsistent:
  - Do NOT change dates, durations, or year ranges.
  - Do NOT change counts such as "10+ papers", "800 individuals", or similar.
  - Do NOT promote "assisted" or "contributed" into "led", "owned", or "managed"
    unless the original wording explicitly supports that.
- Do NOT introduce strong impact adjectives such as "dramatically",
  "significantly", or "substantially" unless the original resume already uses
  equivalent language or metrics.
- Keep the level of strength and certainty in the wording aligned with the
  original text.
- If a section is empty in the original resume, you MUST leave it empty.

You may:
- Rephrase bullet points and descriptions for clarity and impact, while
  preserving the same factual content and level of strength.
- Reorder content to better highlight relevance to the job.
- Emphasize experiences, skills, and projects that match the job description
  and the provided mapping.

You will receive:
- A structured resume.
- A structured mapping_result with matched_skills, matched_requirements, gaps,
  and match_score.

You must return a structured FullEnhancementOutput object with:
- summary (optional): enhanced summary + reasons for changes.
- experiences (optional): enhanced list of experiences + reasons.
- educations (optional): enhanced list of educations + reasons.
- skills (optional): enhanced skills list + reasons.
- certifications (optional): enhanced certifications + reasons.
- languages (optional): enhanced languages + reasons.
- projects (optional): enhanced projects + reasons.

Skills section rules:
- The skills list must remain a flat array of Skill objects.
- You may reorder skills so that those matching the job description and
  mapping_result appear first.
- You must NOT remove any skills that appear in the original resume.skills list.
- You must NOT add any new skills that are not present in the original resume.
- You must NOT group skills into categories or nested structures.
- The final enhanced skills set must contain exactly the same skills as the
  original resume.skills, differing only in order.

Section consistency:
- For each section (summary, experiences, educations, skills, certifications,
  languages, projects), treat the enhanced content you return as the
  authoritative replacement for that section.
- Do NOT describe a change in a ChangeReason unless the same change is present
  in the corresponding enhanced content.

For each change you make, add a concise ChangeReason explaining WHAT changed
and WHY it was changed in simple, direct language.

Enhancement philosophy:
- Prefer minimal, high-impact edits over full rewrites.
- Do NOT rephrase content that already aligns well with the job description
  and the mapping_result.
- Only rewrite when it clearly improves relevance, clarity, or keyword
  alignment with the job description.

IMPORTANT RULE (no change → no reason):
- Before writing any ChangeReason, you must internally compare the BEFORE and
  AFTER content for each item (summary, bullet, field, or entry).
- Only add a ChangeReason for an item if its enhanced content is actually
  different from the original.
- If the enhanced content is identical to the original, do NOT generate a
  reason for that item.
- If no meaningful improvement is possible for a field or entry, keep it
  unchanged and allow the corresponding reasons list (or that item's reasons)
  to be empty. Do not force changes.

ChangeReason quality rules:
- Use clear, concrete, non-marketing language. Avoid buzzwords and overly
  fancy phrases.
- Do NOT use vague reasons such as "Rephrased for clarity",
  "Improved readability", or "Enhanced impact" without specifics.
- Each reason must explicitly:
  - describe what changed (before vs after, in summary form), and
  - state which job responsibility, requirement, or mapping_result element
    this change supports, or how it makes the resume easier for a human
    recruiter to understand.
- Prefer simple patterns such as:
  "Changed X to Y to highlight Z from the job description."
  "Shortened X to make the responsibility easier to read."
"""

ENHANCE_USER_TEMPLATE = """## Resume (structured)
{resume_json}

## Mapping result (structured)
{mapping_result_json}

Enhance the resume section by section following the rules and return a
FullEnhancementOutput object."""


def build_enhance_prompt_user(resume_json: str, mapping_result_json: str) -> str:
    """Build the user message for the enhancement LLM call."""
    return ENHANCE_USER_TEMPLATE.format(
        resume_json=resume_json,
        mapping_result_json=mapping_result_json,
    )


def build_section_prompt_user(
    section_name: str,
    resume_json: str,
    mapping_result_json: str
) -> str:
    """
    Build prompt for enhancing a single section.
    
    Args:
        section_name: One of: summary, experiences, educations, skills,
                      certifications, languages, projects
        resume_json: Full resume as JSON string
        mapping_result_json: Mapping result as JSON string
    
    Returns:
        Prompt string for the LLM
    """
    section_display = section_name.replace("_", " ").title()
    
    return f"""## Resume (structured)
{resume_json}

## Mapping result (structured)
{mapping_result_json}

## Task
Enhance ONLY the '{section_display}' section of the resume following these rules:

1. Do NOT invent or fabricate information.
2. Do NOT add technologies not in the original resume.
3. Do NOT change factual quantities such as dates, durations, or counts unless
   there is a clear inconsistency in the original resume.
4. Enhancement philosophy:
   - Prefer minimal, high-impact edits over full rewrites.
   - Use natural, human-sounding language: clear, professional, and simple.
     Avoid overly formal, robotic, or buzzword-heavy phrasing.
   - Do not rephrase content that already aligns well with the job description
     and mapping_result.
   - Only rewrite when it clearly improves relevance, clarity, or keyword
     alignment.
5. Before changing any item in this section, ask:
   "Does this already strongly align with the job description and mapping?"
   If yes, keep it mostly unchanged.
6. IMPORTANT (no change → no reason):
   - Only create a ChangeReason for an item if its enhanced content is
     actually different from the original.
   - If the enhanced content is identical, do NOT create a reason for that
     item.
   - If no meaningful improvement is possible, keep the item unchanged and
     allow its reasons list to be empty.
7. Keep all facts consistent with the original.
8. If the section is empty in the original, leave it empty.

Additional rules for the 'Skills' section:
- If section_name == "skills":
  - Do NOT remove any skills that appear in the original resume.skills.
  - Do NOT add any new skills that are not present in the original resume.
  - Only reorder the existing skills so that those most relevant to the job
    description and mapping_result appear first.
  - Keep the structure as a flat list of skill objects (no grouping or nested
    categories).

Additional rules for 'Experiences' and 'Projects' sections:
- If section_name in ["experiences", "projects"]:
  - Do NOT create new experience or project entries; each enhanced item must
    correspond to an existing one in the original resume.
  - You may split long bullets into multiple simpler bullets, or merge very
    short, redundant bullets, while preserving the same factual content.
  - Do NOT introduce new tools, metrics, or responsibilities that are not
    clearly implied by the original text.

Return a {section_name.capitalize()}EnhancementOutput object with:
- enhanced: The enhanced {section_display} content
- reasons: List of ChangeReason objects explaining each actual change
"""
