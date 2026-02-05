# from google import genai
# import os
# from dotenv import load_dotenv

# load_dotenv()

# class GeminiClient:
#     def __init__(self):
#         api_key = os.getenv("GEMINI_API_KEY")
#         if not api_key:
#             raise RuntimeError("GEMINI_API_KEY is not set")

#         self.client = genai.Client(api_key=api_key)
#         self.model_name = os.getenv("GEMINI_LLM_MODEL", "gemini-2.5-flash")

#     async def generate_json(self, prompt: str) -> str:
#         # الدالة generate_content هي sync → ما بدها await
#         response = self.client.models.generate_content(
#             model=self.model_name,
#             contents=prompt,
#             config={
#                 "temperature": 0.1,
#                 "max_output_tokens": 8192,
#                 "response_mime_type": "application/json"
#             },
#         )
#         return response.text

# gemini_client = GeminiClient()




from google import genai
import os
import json
from dotenv import load_dotenv

load_dotenv()


class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")

        self.client = genai.Client(api_key=api_key)
        self.model_name = os.getenv("GEMINI_LLM_MODEL", "gemini-2.5-flash")

    # ✅ هاي متل ما هي (للـ Resume Parser)
    async def generate_json(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "temperature": 0.1,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json"
            },
        )
        return response.text

    # ✅ دالة جديدة للـ Job Parser
    async def generate_json_dict(self, prompt: str) -> dict:
        json_text = await self.generate_json(prompt)

        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            raise ValueError(
                f"Gemini returned invalid JSON:\n{json_text}"
            )


gemini_client = GeminiClient()
