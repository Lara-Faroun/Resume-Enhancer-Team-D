import json
import ast
import html
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
import requests
from services import ResumeEnhancerAPI
from config import AppConfig
from assets.icons import ICONS


PROGRESS_AFTER_PARSE = AppConfig.PROGRESS_AFTER_PARSE
PROGRESS_MAPPING_START = AppConfig.PROGRESS_MAPPING_START
PROGRESS_AFTER_MAPPING = AppConfig.PROGRESS_AFTER_MAPPING
PROGRESS_SECTIONS_START = AppConfig.PROGRESS_SECTIONS_START
PROGRESS_SECTIONS_END = AppConfig.PROGRESS_SECTIONS_END
PROGRESS_COMPLETE = AppConfig.PROGRESS_COMPLETE


def _progress_fraction(percent_0_100: float) -> float:
    return min(100, max(0, percent_0_100)) / 100


def _format_date(value) -> str:
    if value is None or value == "":
        return ""
    s = str(value).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%b %Y")
        except ValueError:
            pass
    try:
        if s.endswith("Z"):
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return dt.strftime("%b %Y")
        dt = datetime.fromisoformat(s)
        return dt.strftime("%b %Y")
    except Exception:
        return s


def _try_parse_payload(value):
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return value
    if not isinstance(value, str):
        return None
    t = value.strip()
    if not t:
        return None
    if not (t.startswith("{") or t.startswith("[")):
        return None
    try:
        return json.loads(t)
    except Exception:
        pass
    try:
        return ast.literal_eval(t)
    except Exception:
        return None


def _unwrap_stream_payload(section: str, payload):
    if not isinstance(payload, dict):
        return payload
    if "enhanced" in payload:
        return payload["enhanced"]
    for key in ("data", "payload", "result", section):
        if key in payload:
            return payload[key]
    return payload


def _payload_to_markdown(section: str, payload) -> str:
    if payload is None:
        return ""

    if isinstance(payload, dict) and section in payload:
        payload = payload[section]

    if section == "summary":
        if isinstance(payload, str):
            return payload.strip()
        if isinstance(payload, dict):
            for k in ("text", "summary", "enhanced"):
                if k in payload and isinstance(payload[k], str):
                    return payload[k].strip()

    if section == "skills" and isinstance(payload, list):
        lines = []
        for item in payload:
            if isinstance(item, dict):
                name = item.get("skill_name") or item.get("name") or ""
                typ = item.get("skill_type") or item.get("type") or ""
                if name and typ:
                    lines.append(f"- **{name}** ({typ})")
                elif name:
                    lines.append(f"- **{name}**")
            elif isinstance(item, str) and item.strip():
                lines.append(f"- {item.strip()}")
        return "\n".join(lines) if lines else ""

    if section == "certifications" and isinstance(payload, list):
        lines = []
        for c in payload:
            if isinstance(c, dict):
                name = c.get("certification_name") or c.get("name") or ""
                org = c.get("issuing_organization") or c.get("issuer") or ""
                d = _format_date(c.get("issue_date") or c.get("date") or c.get("issued") or "")
                meta = " — ".join([x for x in [org, d] if x])
                lines.append(f"- **{name}**" + (f" ({meta})" if meta else ""))
        return "\n".join(lines) if lines else ""

    if section == "languages" and isinstance(payload, list):
        lines = []
        for l in payload:
            if isinstance(l, dict):
                lang = l.get("language") or ""
                prof = l.get("proficiency_level") or l.get("level") or ""
                if lang and prof:
                    lines.append(f"- **{lang}** — {prof}")
                elif lang:
                    lines.append(f"- **{lang}**")
        return "\n".join(lines) if lines else ""

    if section == "projects" and isinstance(payload, list):
        out = []
        for p in payload:
            if isinstance(p, dict):
                name = p.get("project_name") or p.get("name") or ""
                link = p.get("project_link") or p.get("link") or ""
                desc = p.get("description") or []
                out.append(f"**{name}**" + (f" — {link}" if link else ""))
                if isinstance(desc, list):
                    out.extend([f"- {d}" for d in desc if str(d).strip()])
                elif isinstance(desc, str) and desc.strip():
                    out.append(f"- {desc.strip()}")
                out.append("")
        return "\n".join(out).strip()

    if isinstance(payload, list):
        if all(isinstance(x, str) for x in payload):
            return "\n".join([f"- {x.strip()}" for x in payload if x.strip()])
        if all(isinstance(x, dict) for x in payload):
            blocks = []
            for d in payload:
                pairs = []
                for k, v in d.items():
                    if v is None or v == "":
                        continue
                    vv = _format_date(v) if "date" in str(k).lower() else v
                    pairs.append(f"- **{k.replace('_',' ').title()}**: {vv}")
                if pairs:
                    blocks.append("\n".join(pairs))
            return "\n\n".join(blocks)

    if isinstance(payload, dict):
        if "enhanced" in payload:
            return _payload_to_markdown(section, payload["enhanced"])
        lines = []
        for k, v in payload.items():
            if v is None or v == "":
                continue
            vv = _format_date(v) if "date" in str(k).lower() else v
            lines.append(f"- **{k.replace('_',' ').title()}**: {vv}")
        return "\n".join(lines)

    return ""


def _extract_enhanced_from_partial(text: str):
    if not isinstance(text, str) or not text.strip():
        return None

    t = text
    key_positions = []
    for needle in ('"enhanced"', "'enhanced'"):
        idx = t.find(needle)
        if idx != -1:
            key_positions.append((idx, needle))
    if not key_positions:
        return None

    idx, needle = sorted(key_positions, key=lambda x: x[0])[0]
    colon = t.find(":", idx + len(needle))
    if colon == -1:
        return None

    i = colon + 1
    n = len(t)
    while i < n and t[i].isspace():
        i += 1
    if i >= n:
        return None

    if t[i] in ('"', "'"):
        quote = t[i]
        i += 1
        out = []
        esc = False
        while i < n:
            ch = t[i]
            if esc:
                out.append(ch)
                esc = False
            else:
                if ch == "\\":
                    esc = True
                elif ch == quote:
                    break
                else:
                    out.append(ch)
            i += 1
        return "".join(out)

    if t[i] in ("[", "{"):
        start = i
        stack = []
        in_str = False
        str_q = ""
        esc = False

        def push(c):
            stack.append(c)

        def pop(c):
            if not stack:
                return
            top = stack[-1]
            if (top == "[" and c == "]") or (top == "{" and c == "}"):
                stack.pop()

        while i < n:
            ch = t[i]
            if in_str:
                if esc:
                    esc = False
                else:
                    if ch == "\\":
                        esc = True
                    elif ch == str_q:
                        in_str = False
                i += 1
                continue

            if ch in ('"', "'"):
                in_str = True
                str_q = ch
            elif ch in ("[", "{"):
                push(ch)
            elif ch in ("]", "}"):
                pop(ch)
                if not stack:
                    frag = t[start : i + 1]
                    parsed = _try_parse_payload(frag)
                    return parsed if parsed is not None else frag
            i += 1

        return None

    return None


def _strip_markdown_for_live(s: str) -> str:
    if not s:
        return ""
    s = s.replace("**", "")
    s = s.replace("__", "")
    s = s.replace("`", "")
    return s


def _typewriter_component(section_key: str, text: str, speed_ms: int = 35) -> str:
    safe_text = html.escape(text or "")
    key = html.escape(section_key)
    return f"""
<div id="tw_{key}" style="white-space:pre-wrap; font-size: 1rem; line-height: 1.6;"></div>
<script>
(function() {{
  const key = "{key}";
  const target = `{safe_text}`;
  window.__twStore = window.__twStore || {{}};
  const store = window.__twStore;

  if (!store[key]) {{
    store[key] = {{cur:"", target:"", running:false}};
  }}
  store[key].target = target;

  const el = document.getElementById("tw_{key}");
  if (!el) return;

  function renderCursor(txt) {{
    return txt + "▍";
  }}

  function tick() {{
    const s = store[key];
    if (!s) return;
    if (s.cur.length < s.target.length) {{
      const nextLen = Math.min(s.cur.length + 1, s.target.length);
      s.cur = s.target.slice(0, nextLen);
      el.textContent = renderCursor(s.cur);
      setTimeout(tick, {speed_ms});
    }} else {{
      el.textContent = s.cur;
      s.running = false;
    }}
  }}

  if (!store[key].running) {{
    store[key].running = true;
    if (store[key].cur.length > store[key].target.length) {{
      store[key].cur = store[key].target;
    }}
    tick();
  }}
}})();
</script>
"""


def render_processing_section():
    st.markdown(
        """
        <div class="step-card">
            <div class="step-header">
                <div class="step-number">2</div>
                <div class="step-title">AI Processing</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.processing:
        if st.session_state.get("enhance_result"):
            status = st.session_state.enhance_result.get("status", "complete")
            st.session_state.step = 3 if status == "complete" else 4
            st.rerun()
            return

        st.info("Ready to process your CV with AI")

        if st.button("Start Processing", use_container_width=True, type="primary"):
            st.session_state.processing = True
            st.rerun()
        return

    st.markdown("<div class='progress-processing'>", unsafe_allow_html=True)
    progress_bar = st.progress(_progress_fraction(0))
    st.markdown("</div>", unsafe_allow_html=True)

    status_text = st.empty()

    st.markdown("---")

    header_placeholder = st.empty()

    def render_live_header(state: str):
        if state == "processing":
            header_placeholder.markdown(
                f"### <span class='icon-spin icon-spinner'>{ICONS['spinner']}</span> Live Progress",
                unsafe_allow_html=True,
            )
        elif state == "complete":
            header_placeholder.markdown(
                f"### {ICONS['check']} Processing Complete",
                unsafe_allow_html=True,
            )
        elif state == "error":
            header_placeholder.markdown(
                f"### {ICONS['x_circle']} Processing Failed",
                unsafe_allow_html=True,
            )

    render_live_header("processing")

    col1, col2 = st.columns(2)
    with col1:
        progress_display = st.empty()
    with col2:
        stage_display = st.empty()

    st.markdown("---")
    sections_container = st.container()

    try:
        api_client = ResumeEnhancerAPI()

        progress_bar.progress(_progress_fraction(PROGRESS_AFTER_PARSE))
        status_text.markdown(
            f"### <span class='icon-spin icon-spinner'>{ICONS['spinner']}</span> Uploading and parsing CV...",
            unsafe_allow_html=True,
        )

        parse_result = api_client.parse_resume(
            st.session_state.uploaded_file, st.session_state.job_description
        )
        st.session_state.parse_result = parse_result

        progress_bar.progress(_progress_fraction(PROGRESS_AFTER_PARSE))
        status_text.markdown(
            f"<span class='icon-pulse'>{ICONS['robot']}</span> Starting AI enhancement (streaming mode)...",
            unsafe_allow_html=True,
        )

        section_containers = {}
        display_pct = PROGRESS_AFTER_PARSE

        for event in api_client.enhance_resume_streaming(
            parse_result["resume"], parse_result["job_description"]
        ):
            event_type = event.get("event_type", "")
            progress_percent = event.get("progress_percent", 0)

            if event_type == "mapping_start":
                stage_display.info("Mapping")
                status_text.markdown(
                    f"<span class='icon-pulse'>{ICONS['search']}</span> Analyzing CV and job description...",
                    unsafe_allow_html=True,
                )
                display_pct = PROGRESS_MAPPING_START

            elif event_type == "mapping_complete":
                match_score = event.get("match_score", 0)
                score_pct = int(match_score * 10)
                if match_score >= AppConfig.MIN_MATCH_SCORE:
                    stage_display.success(f"Match: {score_pct}%")
                else:
                    stage_display.warning(f"Match: {score_pct}%")
                display_pct = PROGRESS_AFTER_MAPPING

            elif event_type == "section_start":
                section = event.get("section", "")
                title = section.replace("_", " ").title()

                status_text.markdown(
                    f"### <span class='icon-spin icon-spinner'>{ICONS['spinner']}</span> Enhancing {title}...",
                    unsafe_allow_html=True,
                )
                stage_display.info(title)

                with sections_container:
                    st.markdown(f"#### {title}", unsafe_allow_html=True)
                    section_containers[section] = st.empty()

                display_pct = PROGRESS_SECTIONS_START + (progress_percent / 100) * (
                    PROGRESS_SECTIONS_END - PROGRESS_SECTIONS_START
                )

            elif event_type == "section_delta":
                section = event.get("section", "")
                accumulated_text = event.get("accumulated_text", "")

                if section in section_containers and accumulated_text:
                    parsed = _try_parse_payload(accumulated_text)
                    if parsed is not None:
                        unwrapped = _unwrap_stream_payload(section, parsed)
                    else:
                        unwrapped = _unwrap_stream_payload(section, _extract_enhanced_from_partial(accumulated_text))

                    pretty = _payload_to_markdown(section, unwrapped) if unwrapped is not None else ""
                    live_text = _strip_markdown_for_live(pretty).strip()

                    with section_containers[section]:
                        if live_text:
                            components.html(
                                _typewriter_component(f"{section}", live_text),
                                height=min(260, max(90, 24 + int(len(live_text) / 3))),
                                scrolling=True,
                            )
                        else:
                            st.markdown("_Enhancing…_")

                display_pct = PROGRESS_SECTIONS_START + (progress_percent / 100) * (
                    PROGRESS_SECTIONS_END - PROGRESS_SECTIONS_START
                )

            elif event_type == "section_complete":
                section = event.get("section", "")
                title = section.replace("_", " ").title()

                status_text.markdown(
                    f"{ICONS['check']} Completed {title}",
                    unsafe_allow_html=True,
                )

                partial = event.get("partial_payload", {}).get(section, {})
                enhanced_text = partial.get("enhanced", "")

                if section in section_containers:
                    with section_containers[section]:
                        st.success("Complete")
                        with st.expander("View Full Content"):
                            parsed = _try_parse_payload(enhanced_text)
                            parsed = _unwrap_stream_payload(section, parsed)
                            pretty = _payload_to_markdown(section, parsed) if parsed is not None else ""

                            fallback = enhanced_text
                            if isinstance(fallback, (list, dict)):
                                fallback = json.dumps(fallback, ensure_ascii=False, indent=2)

                            st.markdown(pretty if pretty else fallback)

                display_pct = PROGRESS_SECTIONS_START + (progress_percent / 100) * (
                    PROGRESS_SECTIONS_END - PROGRESS_SECTIONS_START
                )

            elif event_type == "complete":
                state = event.get("state", {})
                st.session_state.enhance_result = {
                    "status": event.get("status", "complete"),
                    "mapping_result": state.get("mapping_result", {}),
                    "enhanced_resume": state.get("enhanced_resume", {}),
                    "report_summary": state.get("report_summary", ""),
                    "feedback_message": state.get("feedback_message", ""),
                }

                display_pct = PROGRESS_COMPLETE
                progress_bar.progress(_progress_fraction(display_pct))

                progress_display.markdown(
                    f"<div style='font-size:2.2rem; font-weight:800; color:#667eea;'>{display_pct:.1f}%</div>",
                    unsafe_allow_html=True,
                )

                stage_display.success("Complete")
                status_text.markdown(
                    f"{ICONS['check']} All sections enhanced.",
                    unsafe_allow_html=True,
                )
                break

            elif event_type == "error":
                raise Exception(event.get("message") or "Unknown error")

            display_pct = min(PROGRESS_COMPLETE, max(0, display_pct))
            progress_bar.progress(_progress_fraction(display_pct))

            progress_display.markdown(
                f"<div style='font-size:2.2rem; font-weight:800; color:#667eea;'>{display_pct:.1f}%</div>",
                unsafe_allow_html=True,
            )

        if not st.session_state.get("error"):
            progress_bar.progress(_progress_fraction(PROGRESS_COMPLETE))

        st.session_state.processing = False

        if st.session_state.get("error"):
            render_live_header("error")
        else:
            render_live_header("complete")

        st.markdown("---")

        if st.button("Final Step", use_container_width=True, type="primary"):
            status = st.session_state.enhance_result.get("status", "complete")
            st.session_state.step = 3 if status == "complete" else 4
            st.rerun()

    except Exception as e:
        st.session_state.error = str(e)
        st.session_state.processing = False
        render_live_header("error")
        status_text.error("Processing failed")

    if st.session_state.error:
        st.error(st.session_state.error)
        with st.expander("Troubleshooting Help"):
            st.markdown(
                f"""
            - Ensure backend is running at `{AppConfig.API_BASE_URL}`
            - Check CV file validity
            - Verify job description format
            - Check backend logs
            """
            )
        if st.button("Try Again", use_container_width=True):
            st.session_state.error = None
            st.session_state.processing = False
            st.session_state.step = 1
            st.rerun()
