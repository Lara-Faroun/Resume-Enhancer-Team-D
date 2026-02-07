import json
import streamlit as st
import httpx

st.set_page_config(page_title="Incremental SSE Viewer", layout="wide")
st.title("Incremental Mode - SSE Viewer (Minimal)")

endpoint = st.text_input("Endpoint", "http://localhost:8000/api/v1/enhance?mode=incremental")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Request JSON")
    payload_text = st.text_area(
        "Body",
        height=420,
        value=json.dumps(
            {
                "resume": {
                    "personal_info": {
                        "full_name": "Test User",
                        "phone_number": "string",
                        "email_address": "user@example.com",
                        "linkedin": "string",
                        "personal_website": "string",
                    },
                    "summary": "string",
                    "educations": [],
                    "experiences": [],
                    "skills": [
                        {"skill_name": "Python", "skill_type": "technical"},
                        {"skill_name": "Communication", "skill_type": "soft"},
                    ],
                    "certifications": [],
                    "languages": [{"language": "English", "proficiency_level": "C1"}],
                    "projects": [],
                },
                "job_description": {
                    "job_title": "Backend Engineer",
                    "company_name": "Example",
                    "responsibilities": ["string"],
                    "requirements": ["string"],
                    "required_skills": ["Python"],
                    "preferred_skills": [],
                    "seniority_level": "mid",
                    "soft_skills": ["Communication"],
                },
                "mode": "incremental",
            },
            indent=2,
        ),
    )

with col2:
    st.subheader("Live SSE Output")
    out = st.empty()
    status_box = st.empty()

run = st.button("Run (Stream)")

def try_parse_json(s: str):
    s = s.strip()
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None

if run:
    # Validate body JSON
    try:
        payload = json.loads(payload_text)
    except Exception as e:
        st.error(f"Body JSON invalid: {e}")
        st.stop()

    lines = []
    out.write("Connecting...")

    try:
        with httpx.Client(timeout=None) as client:
            with client.stream(
                "POST",
                endpoint,
                json=payload,
                headers={"Accept": "text/event-stream"},
            ) as r:
                status_box.info(f"HTTP {r.status_code}")
                # إذا السيرفر رجع JSON عادي بدل SSE، رح نشوفه هون
                if r.status_code != 200:
                    text = r.read().decode("utf-8", errors="replace")
                    status_box.error("Non-200 response")
                    st.code(text)
                    st.stop()

                # Read SSE lines live
                for raw in r.iter_lines():
                    if raw is None:
                        continue

                    line = raw.strip()
                    if not line:
                        continue  # ignore blank separators

                    # Show exactly what comes from server
                    lines.append(line)
                    if len(lines) > 200:
                        lines = lines[-200:]

                    # Friendly render: try parse `data: {json}`
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        parsed = try_parse_json(data_str)
                        if isinstance(parsed, dict):
                            lines[-1] = "data: " + json.dumps(parsed, ensure_ascii=False)
                    out.code("\n".join(lines), language="text")

        status_box.success("Stream ended (connection closed).")

    except Exception as e:
        status_box.error(f"Stream error: {e}")
    