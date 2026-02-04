"""
Sample data for testing the graph workflow before parsing is implemented.
All fixtures conform to the Pydantic schemas in app/schemas.
"""
from .sample_data import sample_resume, sample_job_description

__all__ = ["sample_resume", "sample_job_description"]
