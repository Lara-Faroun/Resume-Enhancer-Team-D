import json
import time
import threading
from collections import deque

import streamlit as st
import httpx

# =============================================================================
# Page
# =============================================================================
st.set_page_config(page_title="LangGraph Runner", layout="wide")
st.title("LangGraph Workflow Runner")

DEFAULT_ENDPOINT = "http://localhost:8000/api/v1/enhance"

# =============================================================================
# Session state init
# =============================================================================
ss = st.session_state

# core state
ss.setdefault("events", [])
ss.setdefault("final_state", None)
ss.setdefault("stream_done", False)
ss.setdefault("demo_mode", False)
ss.setdefault("fallback_triggered", False)
ss.setdefault("last_partial", None)
ss.setdefault("started_at", 0.0)
ss.setdefault("last_event_at", 0.0)

# typewriter
ss.setdefault("tw_active", False)
ss.setdefault("tw_text", "")
ss.setdefault("tw_index", 0)
ss.setdefault("tw_label", "")
ss.setdefault("tw_last_tick", 0.0)
ss.setdefault("tw_speed_ms", 20)
ss.setdefault("tw_target_section", "")

# UI refresh throttling
ss.setdefault("ui_last_rerun_at", 0.0)
ss.setdefault("ui_rerun_every_ms", 100)  # good default

# sections rendering (chat-like)
ss.setdefault(
    "section_order",
    ["summary", "experiences", "educations", "skills", "certifications", "languages", "projects", "report_summary"],
)
ss.setdefault(
    "section_titles",
    {
        "summary": "Summary",
        "experiences": "Experiences",
        "educations": "Educations",
        "skills": "Skills",
        "certifications": "Certifications",
        "languages": "Languages",
        "projects": "Projects",
        "report_summary": "Report Summary",
    },
)
ss.setdefault("section_final", {})  # section -> final text
ss.setdefault("section_typed", {})  # section -> currently typed text
ss.setdefault("section_streaming", {})  # section -> accumulated streaming text (from deltas)
ss.setdefault("section_status", {})  # section -> "streaming" | "complete"

# background worker (for incremental SSE)
ss.setdefault("bg_thread", None)
ss.setdefault("bg_running", False)
ss.setdefault("bg_stop", None)
ss.setdefault("bg_lock", None)
ss.setdefault("bg_events", None)  # deque of raw events from worker
ss.setdefault("bg_sections_buffer", None)  # deque of {"section":..., "label":..., "text":...}
ss.setdefault("bg_error", None)

# =============================================================================
# Demo fallback content (kept)
# =============================================================================
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
    ("Educations (demo)", "Education section kept as-is (already clear and relevant)."),
    ("Skills (demo)", "Python, FastAPI, PostgreSQL, SQL, Docker, CI/CD, Problem Solving, Communication."),
    ("Certifications (demo)", "Relevant backend certification kept as-is (Python/API-focused)."),
    ("Languages (demo)", "Arabic (C2), English (B2)."),
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

# =============================================================================
# Helpers
# =============================================================================
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


def is_quota_429_message(msg: str) -> bool:
    m = (msg or "").lower()
    return ("429" in m) or ("resource_exhausted" in m) or ("quota" in m) or ("rate limit" in m)


def normalize_to_text(x) -> str:
    """Convert list/dict/other types into readable markdown text."""
    if x is None:
        return ""
    if isinstance(x, str):
        return x.strip()

    if isinstance(x, list):
        lines = []
        for item in x:
            s = normalize_to_text(item)
            if not s:
                continue
            lines.append(s)
        # Try to keep bullet feel
        # If items don't look like bullets, add "- "
        if lines and all(not ln.lstrip().startswith(("-", "•")) for ln in lines):
            lines = [f"- {ln}" for ln in lines]
        return "\n".join(lines).strip()

    if isinstance(x, dict):
        for key in ["enhanced", "text", "content", "summary"]:
            if key in x:
                return normalize_to_text(x.get(key))
        try:
            return json.dumps(x, ensure_ascii=False, indent=2)
        except Exception:
            return str(x).strip()

    return str(x).strip()


# =============================================================================
# Typewriter (chat-like)
# =============================================================================
def start_typewriter(section: str, label: str, text):
    text = normalize_to_text(text)
    ss["tw_active"] = True
    ss["tw_target_section"] = section
    ss["tw_label"] = label
    ss["tw_text"] = text
    ss["tw_index"] = 0
    ss["tw_last_tick"] = time.time()


def step_typewriter():
    if not ss["tw_active"]:
        return None

    now = time.time()
    if (now - ss["tw_last_tick"]) < (ss["tw_speed_ms"] / 1000.0):
        return None

    ss["tw_last_tick"] = now

    text = ss.get("tw_text") or ""
    words = text.split(" ")
    ss["tw_index"] = min(len(words), ss["tw_index"] + 2)
    typed = " ".join(words[: ss["tw_index"]]).strip()

    sec = ss.get("tw_target_section") or ""
    if sec:
        ss["section_typed"][sec] = typed

    if ss["tw_index"] >= len(words):
        ss["tw_active"] = False
        if sec:
            ss["section_final"][sec] = text
            ss["section_typed"][sec] = text

    return typed


def typewriter_tick_from_buffers():
    """
    If nothing is typing, start next buffered section.
    Always advance typing by one tick.
    """
    if ss.get("bg_lock") and ss.get("bg_sections_buffer") is not None:
        with ss["bg_lock"]:
            if (not ss["tw_active"]) and ss["bg_sections_buffer"]:
                item = ss["bg_sections_buffer"].popleft()
                start_typewriter(item["section"], item["label"], item["text"])

    # advance one tick
    step_typewriter()


# =============================================================================
# Rendering helpers
# =============================================================================
def render_events(events_box):
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
        
        # Skip showing every delta event to reduce noise
        if et == "section_delta":
            # Only show delta events occasionally (every ~4th one based on accumulated length)
            acc_len = len(e.get("accumulated_text", ""))
            if acc_len % 200 > 50:  # Show roughly every 200 chars
                continue

        line = f"- **{et}**"
        if sec:
            line += f" | `{sec}`"
        if status == "fallback":
            line += " | ⚠️ fallback"
        if status == "streaming":
            line += " | 📝 streaming"
        if isinstance(prog, (int, float)):
            line += f" | {prog:.1f}%"
        if et == "section_delta":
            acc_len = len(e.get("accumulated_text", ""))
            line += f" | {acc_len} chars"
        if msg:
            line += f"\n  - {msg[:180]}"
        lines.append(line)

    events_box.markdown("\n".join(lines))


def render_sections_stack(sections_container):
    """
    Render sections in a chat-like stack.
    Shows streaming text in real-time, then switches to typed/final text.
    """
    with sections_container:
        for sec in ss["section_order"]:
            title = ss["section_titles"].get(sec, pretty_section_title(sec))
            status = ss.get("section_status", {}).get(sec)
            
            # Priority: streaming > typed > final
            streaming_text = ss.get("section_streaming", {}).get(sec, "")
            typed_text = ss.get("section_typed", {}).get(sec, "")
            final_text = ss.get("section_final", {}).get(sec, "")
            
            # Show streaming content if section is actively streaming
            if status == "streaming" and streaming_text:
                st.markdown(f"### {title} ⏳")
                # Try to extract readable content from streaming JSON
                display_text = _extract_readable_from_streaming(streaming_text)
                st.markdown(display_text if display_text else f"```\n{streaming_text[:500]}...\n```")
            elif typed_text:
                # Show typewriter progress
                st.markdown(f"### {title}")
                st.markdown(typed_text)
            elif final_text:
                # Show final completed text
                st.markdown(f"### {title}")
                st.markdown(final_text)


def _extract_readable_from_streaming(raw_text: str) -> str:
    """
    Try to extract readable text from streaming JSON chunks.
    The streaming text is partial JSON being built up.
    """
    if not raw_text:
        return ""
    
    text = raw_text.strip()
    
    # If it looks like JSON, try to parse what we can
    if text.startswith("{") or text.startswith("["):
        # Try to find "enhanced" content in partial JSON
        import re
        
        # Look for "enhanced": "..." pattern
        match = re.search(r'"enhanced"\s*:\s*"([^"]*)"?', text)
        if match:
            return match.group(1)
        
        # Look for "enhanced": [...] pattern (for list sections)
        match = re.search(r'"enhanced"\s*:\s*\[(.*)\]?', text, re.DOTALL)
        if match:
            content = match.group(1)
            # Extract text from list items
            items = re.findall(r'"([^"]+)"', content)
            if items:
                return "\n".join(f"- {item}" for item in items[:10])
        
        # Fallback: show truncated raw
        return f"_Streaming..._\n```\n{text[:300]}{'...' if len(text) > 300 else ''}\n```"
    
    # Plain text
    return text


def reset_output():
    ss["events"] = []
    ss["final_state"] = None
    ss["stream_done"] = False
    ss["demo_mode"] = False
    ss["fallback_triggered"] = False
    ss["last_partial"] = None
    ss["started_at"] = 0.0
    ss["last_event_at"] = 0.0
    ss["bg_error"] = None

    ss["tw_active"] = False
    ss["tw_text"] = ""
    ss["tw_index"] = 0
    ss["tw_label"] = ""
    ss["tw_last_tick"] = 0.0
    ss["tw_target_section"] = ""

    ss["section_final"] = {}
    ss["section_typed"] = {}
    ss["section_streaming"] = {}
    ss["section_status"] = {}

    ss["ui_last_rerun_at"] = 0.0


def stop_background_worker():
    if ss.get("bg_stop") is not None:
        ss["bg_stop"].set()
    t = ss.get("bg_thread")
    if t and t.is_alive():
        # don't block too long
        t.join(timeout=0.2)
    ss["bg_thread"] = None
    ss["bg_running"] = False
    ss["bg_stop"] = None


def ensure_bg_structures():
    if ss.get("bg_lock") is None:
        ss["bg_lock"] = threading.Lock()
    if ss.get("bg_events") is None:
        ss["bg_events"] = deque()
    if ss.get("bg_sections_buffer") is None:
        ss["bg_sections_buffer"] = deque()
    if ss.get("bg_stop") is None:
        ss["bg_stop"] = threading.Event()


def push_section_to_buffer(section: str, label: str, text):
    text = normalize_to_text(text)
    if not text:
        return
    with ss["bg_lock"]:
        ss["bg_sections_buffer"].append({"section": section, "label": label, "text": text})


def push_event(ev: dict):
    with ss["bg_lock"]:
        ss["bg_events"].append(ev)
        # cap
        while len(ss["bg_events"]) > 800:
            ss["bg_events"].popleft()


def drain_bg_events_into_state():
    """Move worker events deque into ss['events'] list (UI thread)."""
    if ss.get("bg_events") is None or ss.get("bg_lock") is None:
        return
    drained = []
    with ss["bg_lock"]:
        while ss["bg_events"]:
            drained.append(ss["bg_events"].popleft())
    if drained:
        ss["events"].extend(drained)
        if len(ss["events"]) > 800:
            ss["events"] = ss["events"][-800:]


# =============================================================================
# Demo fallback (chat-like)
# =============================================================================
def trigger_demo_fallback(reason: str):
    if ss["fallback_triggered"]:
        return
    ss["fallback_triggered"] = True
    ss["demo_mode"] = True
    ss["bg_error"] = reason

    ss["events"].append(
        {
            "event_type": "error",
            "status": "error",
            "error_message": f"Switching to DEMO mode: {reason}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    )

    # enqueue demo sections into the same buffer, so typewriter shows them chat-like
    ensure_bg_structures()
    for label, text in FALLBACK_SECTIONS:
        key = label.split(" ")[0].lower()
        if key == "report":
            key = "report_summary"
        push_section_to_buffer(key, label, text)

    ss["final_state"] = {
        "mode": "incremental",
        "status": "complete",
        "demo_mode": True,
        "message": "Simulated output because real AI failed (quota/rate limit).",
    }
    ss["stream_done"] = True


# =============================================================================
# Background worker for SSE incremental mode (the key to chat-like UX)
# =============================================================================
def incremental_worker(url: str, body: dict):
    """
    Runs SSE request in a background thread.
    - pushes events to bg_events deque
    - handles section_delta events for real-time streaming
    - pushes enhanced section texts to bg_sections_buffer deque on section_complete
    """
    try:
        with httpx.Client(timeout=None, trust_env=False) as client:
            headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
            with client.stream("POST", url, json=body, headers=headers) as r:
                r.raise_for_status()

                for ev in iter_sse_json_from_raw(r):
                    if ss["bg_stop"].is_set():
                        break

                    push_event(ev)

                    et = ev.get("event_type")
                    sec = ev.get("section")
                    msg = (ev.get("error_message") or "")
                    
                    if et == "error":
                        # stop on error; UI will switch to demo
                        ss["bg_error"] = msg or "Unknown SSE error"
                        break
                    
                    # Handle mapping events
                    if et == "mapping_start":
                        with ss["bg_lock"]:
                            ss["section_status"]["mapping"] = "streaming"
                    
                    if et == "mapping_complete":
                        with ss["bg_lock"]:
                            ss["section_status"]["mapping"] = "complete"
                    
                    # Handle section_start - mark section as streaming
                    if et == "section_start" and sec:
                        with ss["bg_lock"]:
                            ss["section_status"][sec] = "streaming"
                            ss["section_streaming"][sec] = ""  # Reset accumulated text
                    
                    # Handle section_delta - real-time text chunks
                    if et == "section_delta" and sec:
                        accumulated = ev.get("accumulated_text", "")
                        if accumulated:
                            with ss["bg_lock"]:
                                ss["section_streaming"][sec] = accumulated
                                ss["section_status"][sec] = "streaming"
                    
                    # Handle section_complete - final text
                    if et == "section_complete":
                        partial = ev.get("partial_payload") or {}
                        
                        # Extract enhanced text robustly:
                        enhanced_text = ""
                        if isinstance(partial, dict) and sec:
                            if sec in partial and isinstance(partial.get(sec), dict):
                                enhanced_text = normalize_to_text((partial.get(sec) or {}).get("enhanced"))
                            else:
                                # some servers might send { "enhanced": "..."} directly
                                enhanced_text = normalize_to_text(partial.get("enhanced") or "")

                        if enhanced_text and sec:
                            # Mark section as complete with final text
                            with ss["bg_lock"]:
                                ss["section_status"][sec] = "complete"
                                ss["section_streaming"][sec] = ""  # Clear streaming buffer
                            # Push to typewriter buffer for final display
                            push_section_to_buffer(sec, f"{pretty_section_title(sec)} (real)", enhanced_text)

                    if et == "complete":
                        # Handle report_summary from final state
                        state = ev.get("state") or {}
                        rs = state.get("report_summary")
                        if rs:
                            push_section_to_buffer("report_summary", "Report Summary", rs)
                        break

    except httpx.HTTPStatusError as e:
        ss["bg_error"] = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
    except Exception as e:
        ss["bg_error"] = f"Incremental worker failed: {e}"
    finally:
        ss["bg_running"] = False


# =============================================================================
# UI layout
# =============================================================================
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Request")
    endpoint = st.text_input("Endpoint", value=DEFAULT_ENDPOINT)
    mode = st.selectbox("Mode", options=["legacy", "incremental", "sectional"], index=1)

    st.caption("**legacy**: single LLM call | **incremental**: SSE streaming (chat-like UI) | **sectional**: per-section with fallbacks")

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

    ss["tw_speed_ms"] = int(st.slider("Typewriter speed (ms per tick)", 5, 80, int(ss["tw_speed_ms"]), 1))
    ss["ui_rerun_every_ms"] = int(st.slider("UI refresh interval (ms)", 30, 250, int(ss["ui_rerun_every_ms"]), 5))

    col_btns = st.columns(3)
    run_btn = col_btns[0].button("Run", type="primary")
    stop_btn = col_btns[1].button("Stop")
    clear_btn = col_btns[2].button("Clear output")


with col_right:
    st.subheader("Output")
    status_box = st.empty()
    progress_bar = st.progress(0)
    current_section = st.empty()

    st.markdown("#### Enhanced Sections (chat-like)")
    sections_container = st.container()

    st.markdown("#### Sectional Mode Summary")
    sectional_summary_box = st.empty()

    st.markdown("#### Typewriter (indicator)")
    tw_title = st.empty()

    st.markdown("#### Latest partial payload")
    partial_box = st.empty()

    st.markdown("#### Live events (last 12)")
    events_box = st.empty()

    st.markdown("#### Final state")
    final_box = st.empty()


# =============================================================================
# Buttons behavior
# =============================================================================
if stop_btn:
    stop_background_worker()

if clear_btn:
    stop_background_worker()
    reset_output()

# =============================================================================
# Run
# =============================================================================
if run_btn:
    stop_background_worker()
    reset_output()
    ss["started_at"] = time.time()

    try:
        resume = parse_json_field("Resume", resume_json)
        job_description = parse_json_field("Job Description", job_desc_json)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    # ✅ FIX: mode goes in URL query only (NOT in body) to avoid 422
    body = {"resume": resume, "job_description": job_description}
    url = ensure_mode_in_url(endpoint, mode)

    if mode == "legacy":
        status_box.info("Running legacy...")
        try:
            with httpx.Client(timeout=None, trust_env=False) as client:
                r = client.post(url, json=body, headers={"Accept": "application/json"})
                r.raise_for_status()
                result = r.json()
                ss["final_state"] = result
                ss["stream_done"] = True

                rs = result.get("report_summary")
                if rs:
                    ensure_bg_structures()
                    push_section_to_buffer("report_summary", "Report Summary", rs)

        except Exception as e:
            trigger_demo_fallback(f"Legacy request failed: {e}")

    elif mode == "sectional":
        status_box.info("Running sectional mode (per-section with fallbacks)...")
        try:
            with httpx.Client(timeout=None, trust_env=False) as client:
                r = client.post(url, json=body, headers={"Accept": "application/json"})
                r.raise_for_status()
                result = r.json()
                ss["final_state"] = result
                ss["stream_done"] = True

                rs = result.get("report_summary")
                if rs:
                    ensure_bg_structures()
                    push_section_to_buffer("report_summary", "Report Summary", rs)

        except Exception as e:
            trigger_demo_fallback(f"Sectional request failed: {e}")

    else:
        # incremental: start background worker for true chat-like UI
        ensure_bg_structures()
        ss["bg_running"] = True
        ss["bg_error"] = None
        ss["bg_stop"].clear()

        t = threading.Thread(target=incremental_worker, args=(url, body), daemon=True)
        ss["bg_thread"] = t
        t.start()


# =============================================================================
# UI loop (renders chat-like while worker is running or typewriter is active)
# =============================================================================
# 1) Drain background events into UI state
drain_bg_events_into_state()

# 2) Update UI widgets from last event
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
        if last.get("partial_payload") is not None:
            ss["last_partial"] = last.get("partial_payload")
    elif et == "error":
        current_section.error(last.get("error_message", "Error"))
    elif et == "complete":
        current_section.success("Completed ✅")
        if last.get("state") is not None:
            ss["final_state"] = last.get("state")
            ss["stream_done"] = True
else:
    progress_bar.progress(0)
    current_section.info("Waiting...")

# 3) If incremental worker ended with error -> switch to demo (once)
if ss.get("bg_error") and (not ss["demo_mode"]) and (not ss["fallback_triggered"]):
    msg = ss["bg_error"]
    if is_quota_429_message(msg):
        trigger_demo_fallback(f"Quota/rate limit: {msg}")
    else:
        trigger_demo_fallback(f"Real AI error: {msg}")

# 4) Typewriter tick (pull from buffered completed sections)
typewriter_tick_from_buffers()

# 5) Status line (IMPORTANT: don't show "Done" just because backend completed;
#    show done when backend done AND typing/buffer are finished)
typing_left = ss["tw_active"]
buffer_left = False
if ss.get("bg_lock") and ss.get("bg_sections_buffer") is not None:
    with ss["bg_lock"]:
        buffer_left = bool(ss["bg_sections_buffer"])

backend_running = bool(ss.get("bg_running"))
backend_done = (not backend_running) and ss.get("bg_thread") is not None and (not ss.get("bg_thread").is_alive())

if ss["demo_mode"]:
    status_box.warning("Demo mode: simulated output (real AI failed).")
elif backend_running:
    status_box.info("Streaming incremental (chat-like)...")
elif backend_done and (typing_left or buffer_left):
    status_box.info("Finishing typing...")
elif ss["stream_done"] and ss["final_state"] and (not typing_left) and (not buffer_left):
    status_box.success("Done.")
else:
    status_box.info("Idle.")

# 6) Sectional summary display (kept)
if ss["final_state"] and ss["final_state"].get("sectional_metadata"):
    meta = ss["final_state"]["sectional_metadata"]
    section_errors = ss["final_state"].get("section_errors", {})

    succeeded = meta.get("sections_succeeded", 0)
    failed = meta.get("sections_failed", 0)
    total = meta.get("total_sections", 7)
    total_time = meta.get("total_time_ms", 0)

    if failed == 0:
        sectional_summary_box.success(f"✅ **All {succeeded}/{total} sections enhanced successfully** in {total_time:.0f}ms")
    else:
        summary_md = f"⚠️ **{succeeded}/{total} sections enhanced**, {failed} used fallback ({total_time:.0f}ms)\n\n"
        summary_md += "**Failed sections (using original data):**\n"
        for section, error in section_errors.items():
            summary_md += f"- `{section}`: {error[:100]}...\n" if len(error) > 100 else f"- `{section}`: {error}\n"
        sectional_summary_box.warning(summary_md)
else:
    sectional_summary_box.empty()

# 7) Render sections (chat-like)
render_sections_stack(sections_container)

# 8) Typewriter indicator
if ss.get("tw_label"):
    tw_title.info(f"Typing: {ss['tw_label']}")
else:
    tw_title.empty()

# 9) Partial payload
if ss["last_partial"]:
    partial_box.json(ss["last_partial"])
else:
    partial_box.empty()

# 10) Events
render_events(events_box)

# 11) Final state
if ss["final_state"]:
    final_box.json(ss["final_state"])
else:
    final_box.empty()

# 12) Check if there's any streaming content being displayed
streaming_active = any(
    ss.get("section_status", {}).get(sec) == "streaming" 
    for sec in ss["section_order"]
)

# 13) Keep UI alive while:
# - backend streaming thread is running
# - or buffered sections exist
# - or typewriter is active
# - or sections are actively streaming
need_live = backend_running or typing_left or buffer_left or streaming_active
if need_live:
    now = time.time()
    if (now - ss["ui_last_rerun_at"]) * 1000 >= ss["ui_rerun_every_ms"]:
        ss["ui_last_rerun_at"] = now
        st.rerun()
