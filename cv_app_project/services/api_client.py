import requests
import json
from config.settings import AppConfig

class ResumeEnhancerAPI:
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or AppConfig.API_BASE_URL
        self.timeout = AppConfig.API_TIMEOUT
    
    def parse_resume(self, file, job_description: str) -> dict:
        url = f"{self.base_url}{AppConfig.API_PARSE_ENDPOINT}"
        
        files = {
            'file': (file.name, file.getvalue(), file.type or 'application/octet-stream')
        }
        data = {
            'job_description': job_description
        }
        
        response = requests.post(url, files=files, data=data, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def enhance_resume_streaming(self, resume_data: dict, job_description_data: dict):
        """
        Stream-enabled enhance endpoint using SSE (Server-Sent Events).
        
        Yields events as they arrive from the backend:
        - mapping_start
        - mapping_complete
        - section_start
        - section_delta
        - section_complete
        - complete
        """
        url = f"{self.base_url}{AppConfig.API_ENHANCE_ENDPOINT}?mode=incremental"
        
        payload = {
            'resume': resume_data,
            'job_description': job_description_data
        }
        
        headers = {
            'Accept': 'text/event-stream',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            url, 
            json=payload,
            headers=headers,
            timeout=self.timeout,
            stream=True
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                
                if decoded_line.startswith('data: '):
                    json_str = decoded_line[6:]
                    
                    try:
                        event = json.loads(json_str)
                        yield event
                    except json.JSONDecodeError:
                        continue
    
    def enhance_resume(self, resume_data: dict, job_description_data: dict) -> dict:
        """
        Legacy (non-streaming) enhance endpoint.
        Returns complete result in one response.
        """
        url = f"{self.base_url}{AppConfig.API_ENHANCE_ENDPOINT}"
        
        payload = {
            'resume': resume_data,
            'job_description': job_description_data
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def export_resume(self, resume_data: dict, file_type: str = "pdf") -> bytes:
        """
        Export a resume as PDF or DOCX using the backend.
        
        FastAPI route (in your backend):
        @router.post("/export/resume")
        def export_resume(resume: Resume, file_type: Literal["pdf", "docx"] = Query(..., alias="type"))
        
        That signature expects the JSON body to be the Resume model directly,
        not wrapped in an outer { "resume": ... } object.
        """
        url = f"{self.base_url}{AppConfig.API_EXPORT_RESUME_ENDPOINT}"
        params = {"type": file_type}
        response = requests.post(url, json=resume_data, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.content
    
    def health_check(self) -> dict:
        url = f"{self.base_url}/health"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()