from typing import Dict
import re

# Copied from enhance.py for isolated testing to avoid dependency issues
def split_resume_sections(text: str) -> Dict[str, str]:
    """
    Split a resume string into sections (e.g. Skills, Experience, Education).
    Returns a dict { "Skills": "...", "Experience": "...", ... }.
    """
    import re
    
    # Common headers found in resumes
    headers = [
        "SKILLS", "EXPERIENCE", "WORK EXPERIENCE", "EDUCATION", 
        "PROJECTS", "CERTIFICATIONS", "LANGUAGES", "SUMMARY", 
        "OBJECTIVE", "VOLUNTEER"
    ]
    
    # Create a regex pattern to match these headers on their own line or start of line
    # Case insensitive, look for the header followed by newline or colon
    pattern = r'(?:\n|^)\s*(' + '|'.join(headers) + r')\s*(?:\n|:|$)'
    
    matches = list(re.finditer(pattern, text, re.IGNORECASE))
    
    sections = {}
    if not matches:
        return {"Uncategorized": text.strip()}
        
    # Text before the first header is usually personal info or summary if not labeled
    if matches[0].start() > 0:
        sections["Uncategorized"] = text[:matches[0].start()].strip()
        
    for i, match in enumerate(matches):
        header = match.group(1).upper()
        start = match.end()
        
        # End is the start of the next match, or end of string
        if i + 1 < len(matches):
            end = matches[i+1].start()
        else:
            end = len(text)
            
        content = text[start:end].strip()
        # Clean up if header was captured with colon
        if content.startswith(":"):
            content = content[1:].strip()
            
        sections[header] = content
        
    return sections

sample_resume = """
John Doe
Software Engineer

SKILLS
Python, JavaScript, SQL

EXPERIENCE
Software Engineer at Tech Corp
2020 - Present
- Built things.

EDUCATION
BS Computer Science
University of Nowhere

PROJECTS:
Resume Enhancer
- It enhances resumes.
"""

print("Testing split_resume_sections...")
sections = split_resume_sections(sample_resume)
for section, content in sections.items():
    print(f"--- {section} ---")
    print(content)
    print()

expected_sections = ["Uncategorized", "SKILLS", "EXPERIENCE", "EDUCATION", "PROJECTS"]
if all(s in sections for s in expected_sections):
    print("SUCCESS: All expected sections found.")
else:
    print(f"FAILURE: Missing sections. Found: {list(sections.keys())}")
