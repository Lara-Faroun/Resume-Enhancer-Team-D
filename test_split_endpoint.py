import logging
# import pytest
from fastapi.testclient import TestClient
from app.routers.enhance import router
from fastapi import FastAPI

# Setup a minimal app for testing the router
app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_split_endpoint_basic():
    sample_resume = """
    John Doe
    
    SKILLS
    Python, Java
    
    EXPERIENCE
    Dev at Company A
    """
    response = client.post("/split", json={"text": sample_resume})
    assert response.status_code == 200
    data = response.json()
    assert "SKILLS" in data
    assert "EXPERIENCE" in data
    assert "Python, Java" in data["SKILLS"]

def test_split_endpoint_empty():
    response = client.post("/split", json={"text": ""})
    assert response.status_code == 200
    data = response.json()
    assert data == {"Uncategorized": ""}

def test_split_endpoint_no_headers():
    text = "Just some random text without headers."
    response = client.post("/split", json={"text": text})
    assert response.status_code == 200
    data = response.json()
    assert "Uncategorized" in data
    assert data["Uncategorized"] == text

if __name__ == "__main__":
    # Manually run tests if pytest not available or for quick check
    try:
        test_split_endpoint_basic()
        print("test_split_endpoint_basic passed")
        test_split_endpoint_empty()
        print("test_split_endpoint_empty passed")
        test_split_endpoint_no_headers()
        print("test_split_endpoint_no_headers passed")
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
