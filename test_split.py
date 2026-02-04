import sys
import os

# Add 'app' directory to sys.path so that internal imports in enhance.py (like 'from schemas...') work
sys.path.append(os.path.join(os.getcwd(), "app"))

from app.routers.enhance import split_resume_sections

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
