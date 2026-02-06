import json
import time
import streamlit as st
import httpx

st.set_page_config(page_title="LangGraph Runner", layout="wide")
st.title("LangGraph Workflow Runner")

DEFAULT_ENDPOINT = "http://localhost:8000/api/v1/enhance"

# -----------------------------
# Session state
# -----------------------------
ss = st.session_state
ss.setdefault("events", [])
ss.setdefault("final_state", None)
ss.setdefault("stream_done", False)

# typewriter engine
ss.setdefault("tw_active", False)
ss.setdefault("tw_text", "")
ss.setdefault("tw_index", 0)
ss.setdefault("tw_label", "")
ss.setdefault("tw_last_tick", 0.0)
ss.setdefault("tw_speed_ms", 20)

# demo/fallback control
ss.setdefault("demo_mode", False)
ss.setdefault("fallback_triggered", False)
ss.setdefault("last_partial", None)

# streaming status
ss.setdefault("started_at", 0.0)
ss.setdefault("last_event_at", 0.0)


# -----------------------------
# Demo fallback content (shown when real fails)
# -----------------------------
FALLBACK_SECTIONS = [
    (
        "Summary (demo)",
        "Backend software engineer with hands-on experience building RESTful APIs using Python and FastAPI. "
        "Strong grasp of SQL and PostgreSQL, with a focus on scalable, maintainable backend services.",
    ),
    (
        "Experiences (demo)",
        "• Developed and maintained REST APIs using Python and FastAPI.\n"
        "• Integrated PostgreSQL databases and optimized queries for performance.\n"
        "• Collaborated with cross-functional teams to deliver end-to-end features.",
    ),
    (
        "Educations (demo)",
        "Education section kept as-is (already clear and relevant).",
    ),
    (
        "Skills (demo)",
        "Python, FastAPI, PostgreSQL, SQL, Docker, CI/CD, Problem Solving, Communication.",
    ),
    (
        "Certifications (demo)",
        "Relevant backend certification kept as-is (Python/API-focused).",
    ),
    (
        "Languages (demo)",
        "Arabic (C2), English (B2).",
    ),
    (
        "Projects (demo)",
        "AI Resume Enhancer — built an AI-powered resume improvement pipeline; orchestrated multi-step workflows with LangGraph.",
    ),
    (
        "Report Summary (demo)",
        "Demo mode is showing because the real AI call failed (often quota / rate limit). "
        "This simulated output demonstrates the incremental streaming UI and typewriter behavior. "
        "Try again later (or switch provider) for real AI results.",
    ),
]


# -----------------------------
# UI
# -----------------------------
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Request")
    endpoint = st.text_input("Endpoint", value=DEFAULT_ENDPOINT)
    mode = st.selectbox("Mode", options=["legacy", "incremental", "sectional"], index=1)

    st.caption("**legacy**: single LLM call | **incremental**: SSE streaming | **sectional**: per-section with fallbacks")

    resume_json = st.text_area(
        "Resume JSON",
        height=260,
        value=json.dumps(
            {
                "personal_info": {
                    "full_name": "Nour Mansour",
                    "phone_number": "+33-6-12-34-56-78",
                    "email_address": "nour@example.com",
                    "linkedin": "https://www.linkedin.com/in/nour-mansour",
                    "personal_website": "https://github.com/nourm",
                },
                "summary": "Software engineer focused on AI workflow orchestration and scalable backend services.",
                "educations": [],
                "experiences": [],
                "skills": [
                    {"skill_name": "Python", "skill_type": "technical"},
                    {"skill_name": "FastAPI", "skill_type": "technical"},
                    {"skill_name": "Communication", "skill_type": "soft"},
                ],
                "certifications": [],
                "languages": [{"language": "English", "proficiency_level": "C1"}],
                "projects": [],
            },
            indent=2,
        ),
    )

    job_desc_json = st.text_area(
        "Job Description JSON",
        height=260,
        value=json.dumps(
            {
                "job_title": "Backend Software Engineer",
                "company_name": "Innovative Tech GmbH",
                "responsibilities": [
                    "Develop and maintain RESTful APIs",
                    "Collaborate with cross-functional teams",
                ],
                "requirements": [
                    "Strong experience with Python",
                    "Experience building APIs using FastAPI or similar frameworks",
                    "Basic knowledge of relational databases",
                ],
                "required_skills": ["Python", "FastAPI", "SQL"],
                "preferred_skills": ["Docker", "Cloud platforms (AWS or GCP)"],
                "seniority_level": "mid",
                "soft_skills": ["Communication", "Teamwork", "Problem Solving"],
            },
            indent=2,
        ),
    )

    ss["tw_speed_ms"] = int(st.slider("Typewriter speed (ms per tick)", 5, 80, 18, 1))

    col_btns = st.columns(2)
    run_btn = col_btns[0].button("Run", type="primary")
    clear_btn = col_btns[1].button("Clear output")


with col_right:
    st.subheader("Output")
    status_box = st.empty()
    progress_bar = st.progress(0)
    current_section = st.empty()

    st.markdown("#### Sectional Mode Summary")
    sectional_summary_box = st.empty()

    st.markdown("#### Typewriter (real or demo)")
    tw_title = st.empty()
    tw_box = st.empty()

    st.markdown("#### Latest partial payload")
    partial_box = st.empty()

    st.markdown("#### Live events (last 12)")
    events_box = st.empty()

    st.markdown("#### Final state")
    final_box = st.empty()


# -----------------------------
# Helpers
# -----------------------------
def parse_json_field(label: str, text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"{label} is not valid JSON: {e}")


def ensure_mode_in_url(url: str, mode_value: str) -> str:
    if "?" in url:
        if "mode=" in url:
            return url
        return f"{url}&mode={mode_value}"
    return f"{url}?mode={mode_value}"


def iter_sse_json_from_raw(response: httpx.Response):
    buf = ""
    for chunk in response.iter_raw():
        if not chunk:
            continue
        buf += chunk.decode("utf-8", errors="replace")

        while "\n\n" in buf:
            block, buf = buf.split("\n\n", 1)
            block = block.strip()
            if not block:
                continue

            data_lines = []
            for line in block.splitlines():
                line = line.strip()
                if line.startswith("data:"):
                    data_lines.append(line[5:].strip())

            if not data_lines:
                continue

            data_str = "\n".join(data_lines).strip()
            try:
                yield json.loads(data_str)
            except json.JSONDecodeError:
                yield {"event_type": "raw", "data": data_str}


def pretty_section_title(s: str) -> str:
    return (s or "").replace("_", " ").title()


def start_typewriter(label: str, text: str):
    ss["tw_active"] = True
    ss["tw_label"] = label
    ss["tw_text"] = text or ""
    ss["tw_index"] = 0
    ss["tw_last_tick"] = time.time()


def step_typewriter():
    if not ss["tw_active"]:
        return None

    now = time.time()
    if (now - ss["tw_last_tick"]) < (ss["tw_speed_ms"] / 1000.0):
        return None

    ss["tw_last_tick"] = now
    words = ss["tw_text"].split(" ")
    ss["tw_index"] = min(len(words), ss["tw_index"] + 2)

    if ss["tw_index"] >= len(words):
        ss["tw_active"] = False

    return " ".join(words[: ss["tw_index"]]).strip()


def render_events():
    tail = ss["events"][-12:]
    if not tail:
        events_box.markdown("_No events yet_")
        return

    lines = []
    for e in tail:
        et = e.get("event_type", "unknown")
        sec = e.get("section")
        prog = e.get("progress_percent")
        msg = e.get("error_message")
        status = e.get("status")

        line = f"- **{et}**"
        if sec:
            line += f" | `{sec}`"
        if status == "fallback":
            line += " | ⚠️ fallback"
        if isinstance(prog, (int, float)):
            line += f" | {prog:.1f}%"
        if msg:
            line += f"\n  - {msg[:180]}"
        lines.append(line)

    events_box.markdown("\n".join(lines))


def reset_output():
    ss["events"] = []
    ss["final_state"] = None
    ss["stream_done"] = False
    ss["demo_mode"] = False
    ss["fallback_triggered"] = False
    ss["last_partial"] = None

    ss["tw_active"] = False
    ss["tw_text"] = ""
    ss["tw_index"] = 0
    ss["tw_label"] = ""
    ss["tw_last_tick"] = 0.0

    ss["started_at"] = 0.0
    ss["last_event_at"] = 0.0


def is_quota_429_message(msg: str) -> bool:
    m = (msg or "").lower()
    return ("429" in m) or ("resource_exhausted" in m) or ("quota" in m) or ("rate limit" in m)


def trigger_demo_fallback(reason: str):
    if ss["fallback_triggered"]:
        return
    ss["fallback_triggered"] = True
    ss["demo_mode"] = True

    # Add an error event so UI shows why
    ss["events"].append(
        {
            "event_type": "error",
            "status": "error",
            "error_message": f"Switching to DEMO mode: {reason}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    )

    # Simulate events + typewriter
    total = len(FALLBACK_SECTIONS)
    for i, (label, text) in enumerate(FALLBACK_SECTIONS):
        # section_start event
        ss["events"].append(
            {
                "event_type": "section_start",
                "section": label.split(" ")[0].lower(),
                "section_index": i,
                "status": "in_progress",
                "progress_percent": round((i / total) * 100, 1),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )

        # typewriter now
        start_typewriter(label, text)
        while ss["tw_active"]:
            # UI gets updated by the render loop below + rerun
            step_typewriter()
            render_and_rerun_tick()
            time.sleep(0.01)

        # section_complete event with partial
        ss["last_partial"] = {"simulated": {"label": label, "text": text}}
        ss["events"].append(
            {
                "event_type": "section_complete",
                "section": label.split(" ")[0].lower(),
                "section_index": i,
                "status": "complete",
                "progress_percent": round(((i + 1) / total) * 100, 1),
                "partial_payload": ss["last_partial"],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        render_and_rerun_tick()
        time.sleep(0.08)

    # final state
    ss["final_state"] = {
        "mode": "incremental",
        "status": "complete",
        "demo_mode": True,
        "message": "Simulated output because real AI failed (quota/rate limit).",
    }
    ss["events"].append({"event_type": "complete", "status": "complete", "state": ss["final_state"]})
    ss["stream_done"] = True


def render_and_rerun_tick():
    """
    Lightweight render used during demo simulation loop.
    """
    # progress & current section from last event
    if ss["events"]:
        last = ss["events"][-1]
        prog = last.get("progress_percent")
        if isinstance(prog, (int, float)):
            progress_bar.progress(int(max(0, min(100, prog))))

        et = last.get("event_type")
        if et == "section_start":
            current_section.info(f"Running: **{pretty_section_title(last.get('section','?'))}**")
        elif et == "section_complete":
            current_section.success(f"Completed: **{pretty_section_title(last.get('section','?'))}**")
        elif et == "error":
            current_section.error(last.get("error_message", "Error"))
        elif et == "complete":
            current_section.success("Completed ✅")

    # typewriter current text
    if ss.get("tw_label"):
        tw_title.info(f"Typing: {ss['tw_label']}")
    typed = step_typewriter()
    if typed is not None:
        tw_box.markdown(typed)

    # partial payload
    if ss["last_partial"]:
        partial_box.json(ss["last_partial"])

    # events list
    render_events()

    # final
    if ss["final_state"]:
        final_box.json(ss["final_state"])


# -----------------------------
# Clear
# -----------------------------
if clear_btn:
    reset_output()


# -----------------------------
# Run logic
# -----------------------------
if run_btn:
    reset_output()
    ss["started_at"] = time.time()

    try:
        resume = parse_json_field("Resume", resume_json)
        job_description = parse_json_field("Job Description", job_desc_json)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    body = {"resume": resume, "job_description": job_description, "mode": mode}
    url = ensure_mode_in_url(endpoint, mode)

    if mode == "legacy":
        status_box.info("Running legacy...")
        try:
            with httpx.Client(timeout=None, trust_env=False) as client:
                r = client.post(url, json=body, headers={"Accept": "application/json"})
                r.raise_for_status()
                ss["final_state"] = r.json()
                ss["stream_done"] = True
        except Exception as e:
            # legacy failure -> demo fallback
            trigger_demo_fallback(f"Legacy request failed: {e}")

    elif mode == "sectional":
        # Sectional mode: non-streaming, per-section processing with fallbacks
        status_box.info("Running sectional mode (per-section with fallbacks)...")
        progress_bar.progress(10)
        try:
            with httpx.Client(timeout=None, trust_env=False) as client:
                r = client.post(url, json=body, headers={"Accept": "application/json"})
                r.raise_for_status()
                result = r.json()
                ss["final_state"] = result
                ss["stream_done"] = True
                
                # Extract sectional metadata for display
                sectional_meta = result.get("sectional_metadata", {})
                section_errors = result.get("section_errors", {})
                
                # Create synthetic events for UI consistency
                succeeded = sectional_meta.get("succeeded_list", [])
                failed = sectional_meta.get("failed_list", [])
                total = sectional_meta.get("total_sections", 7)
                
                for i, section in enumerate(succeeded):
                    ss["events"].append({
                        "event_type": "section_complete",
                        "section": section,
                        "section_index": i,
                        "status": "complete",
                        "progress_percent": round(((i + 1) / total) * 100, 1),
                    })
                
                for section in failed:
                    ss["events"].append({
                        "event_type": "error",
                        "section": section,
                        "status": "fallback",
                        "error_message": section_errors.get(section, "Unknown error - using original"),
                    })
                
                ss["events"].append({
                    "event_type": "complete",
                    "status": "complete",
                    "state": result,
                })
                
                # Show report summary in typewriter if available
                report_summary = result.get("report_summary")
                if report_summary:
                    start_typewriter("Report Summary", report_summary)
                
        except Exception as e:
            trigger_demo_fallback(f"Sectional request failed: {e}")

    else:
        status_box.info("Streaming incremental...")
        try:
            with httpx.Client(timeout=None, trust_env=False) as client:
                headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
                with client.stream("POST", url, json=body, headers=headers) as r:
                    r.raise_for_status()

                    for ev in iter_sse_json_from_raw(r):
                        ss["last_event_at"] = time.time()
                        ss["events"].append(ev)
                        if len(ss["events"]) > 500:
                            ss["events"] = ss["events"][-500:]

                        et = ev.get("event_type")
                        msg = (ev.get("error_message") or "")

                        # ✅ fallback trigger from SSE error event (this is the key)
                        if et == "error" and not ss["fallback_triggered"]:
                            if is_quota_429_message(msg):
                                trigger_demo_fallback(f"Quota/rate limit: {msg}")
                                break
                            else:
                                trigger_demo_fallback(f"Real AI error: {msg}")
                                break

                        # start typewriter as soon as summary completes (real)
                        if et == "section_complete" and ev.get("section") == "summary":
                            partial = ev.get("partial_payload") or {}
                            ss["last_partial"] = partial
                            enhanced_summary = (partial.get("summary") or {}).get("enhanced")
                            if enhanced_summary:
                                start_typewriter("Summary (real)", enhanced_summary)

                        # update last partial for UI
                        if et == "section_complete" and ev.get("partial_payload"):
                            ss["last_partial"] = ev.get("partial_payload")

                        # on complete: store state + typewriter report
                        if et == "complete":
                            ss["final_state"] = ev.get("state")
                            ss["stream_done"] = True
                            rs = (ss["final_state"] or {}).get("report_summary")
                            if rs:
                                start_typewriter("Report Summary (real)", rs)

        except httpx.HTTPStatusError as e:
            # server non-200 -> demo
            trigger_demo_fallback(f"HTTP error {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            trigger_demo_fallback(f"Incremental request failed: {e}")


# -----------------------------
# Render (works for both real + demo)
# -----------------------------
if ss["demo_mode"]:
    status_box.warning("Demo mode: simulated output (real AI failed).")
else:
    if ss["stream_done"] and ss["final_state"]:
        status_box.success("Done.")
    elif ss["events"]:
        status_box.info("Running...")
    else:
        status_box.info("Idle.")

# Sectional mode summary display
if ss["final_state"] and ss["final_state"].get("sectional_metadata"):
    meta = ss["final_state"]["sectional_metadata"]
    section_errors = ss["final_state"].get("section_errors", {})
    
    succeeded = meta.get("sections_succeeded", 0)
    failed = meta.get("sections_failed", 0)
    total = meta.get("total_sections", 7)
    total_time = meta.get("total_time_ms", 0)
    
    # Build summary display
    if failed == 0:
        sectional_summary_box.success(
            f"✅ **All {succeeded}/{total} sections enhanced successfully** in {total_time:.0f}ms"
        )
    else:
        summary_md = f"⚠️ **{succeeded}/{total} sections enhanced**, {failed} used fallback ({total_time:.0f}ms)\n\n"
        summary_md += "**Failed sections (using original data):**\n"
        for section, error in section_errors.items():
            summary_md += f"- `{section}`: {error[:100]}...\n" if len(error) > 100 else f"- `{section}`: {error}\n"
        sectional_summary_box.warning(summary_md)
else:
    sectional_summary_box.empty()

# progress/current section from last event
if ss["events"]:
    last = ss["events"][-1]
    prog = last.get("progress_percent")
    if isinstance(prog, (int, float)):
        progress_bar.progress(int(max(0, min(100, prog))))
    else:
        # keep progress as-is
        pass

    et = last.get("event_type")
    if et == "section_start":
        current_section.info(f"Running: **{pretty_section_title(last.get('section','?'))}**")
    elif et == "section_complete":
        current_section.success(f"Completed: **{pretty_section_title(last.get('section','?'))}**")
    elif et == "error":
        current_section.error(last.get("error_message", "Error"))
    elif et == "complete":
        current_section.success("Completed ✅")
else:
    progress_bar.progress(0)
    current_section.info("Waiting...")

# typewriter render
if ss.get("tw_label"):
    tw_title.info(f"Typing: {ss['tw_label']}")
else:
    tw_title.empty()

typed = step_typewriter()
if typed is not None:
    tw_box.markdown(typed)

# partial
if ss["last_partial"]:
    partial_box.json(ss["last_partial"])
else:
    partial_box.empty()

# events list
render_events()

# final state
if ss["final_state"]:
    final_box.json(ss["final_state"])
else:
    final_box.empty()

# keep typing smoothly (both real + demo)
if ss["tw_active"]:
    st.experimental_rerun()
