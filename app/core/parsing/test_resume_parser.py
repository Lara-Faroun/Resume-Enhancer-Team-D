import asyncio
from app.core.parsing.resume_parser import parse_resume

import asyncio
from app.core.parsing.text_extractor import extract_text_from_file
from app.core.parsing.resume_parser import parse_resume

print("🚀 test file started")

async def main():
    #Extract
    text = extract_text_from_file("jane_doe_resume4.pdf")

    #Parse
    resume = await parse_resume(text)
    print("✅ resume parsed")
    print(resume.model_dump())

if __name__ == "__main__":
    asyncio.run(main())
