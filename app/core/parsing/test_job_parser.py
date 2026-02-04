import asyncio
from app.core.parsing.job_parser import parse_job_description
import json


job_text_example = """
A software company based in Aleppo is looking for a talented Digital Marketing Specialist to join our team full-time, on-site.
The ideal candidate will have strong hands-on experience in digital marketing and a proven ability to plan, execute, and optimize online marketing campaigns for tech products and services.

Responsibilities:

Plan, execute, and optimize digital marketing campaigns across multiple channels (Meta Ads, Google Ads, TikTok, LinkedIn).

Develop and manage content strategies for social media platforms and websites.

Create and optimize landing pages to improve conversion rates.

Manage SEO and SEM strategies to increase organic and paid traffic.

Monitor campaign performance, analyze data, and provide actionable insights.

Manage marketing budgets and optimize ROI.

Collaborate with design and content teams to deliver high-quality marketing materials.

Conduct market research and competitor analysis.

Support lead generation strategies and work closely with the sales team to improve conversion funnels.

Requirements:

Minimum 2 years of experience in Digital Marketing.

Strong knowledge of paid advertising platforms (Meta, Google, TikTok, LinkedIn).

Good understanding of SEO, SEM, content marketing, and email marketing.

Experience with analytics and tracking tools (Google Analytics, Meta Pixel, conversion tracking).

Ability to analyze data and make data-driven decisions.

Strong communication and organizational skills.

Experience marketing software products or tech services is a strong plus.

Creative mindset with a strong sense of performance marketing.

Work Environment:

Full-time on-site position in Aleppo.

Competitive salary based on experience and skills.

Professional and growth-oriented work environment.

How to Apply:
Please send your CV and any relevant case studies or portfolio links via:
https://wa.me/962782179968

WhatsApp.com (https://wa.me/962782179968)
"""



async def main():
    print("🚀 Job parser test started")

    job_data = await parse_job_description(job_text_example)

    print("✅ Parsed Job Description:")
    print(job_data.model_dump())
    print(json.dumps(job_data.model_dump(), ensure_ascii=False, indent=2))



if __name__ == "__main__":
    asyncio.run(main())
