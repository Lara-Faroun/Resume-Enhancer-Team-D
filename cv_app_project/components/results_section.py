import streamlit as st
from datetime import datetime
from config import AppConfig
from utils import reset_app
from services import ResumeEnhancerAPI
from assets.icons import ICONS
from .cv_comparison import render_cv_comparison
from .feedback_display import render_feedback_display


def render_results_section():
    if not st.session_state.enhance_result:
        st.warning("No results available. Please start from the beginning.")
        if st.button("Go Back"):
            st.session_state.step = 1
            st.rerun()
        return

    enhance_data = st.session_state.enhance_result
    mapping_result = enhance_data.get("mapping_result", {})
    match_score = mapping_result.get("match_score", 0)

    st.markdown(f"""
        <div class="step-card">
            <div class="step-header">
                <div class="step-number">3</div>
                <div class="step-title">{ICONS['check_circle']} Results</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    with col_m1:
        score_pct = int(match_score * 10)
        st.metric("Match Score", f"{score_pct}%")

    with col_m2:
        matched = mapping_result.get("matched_skills", [])
        st.metric("Matched Skills", len(matched))

    with col_m3:
        gaps = mapping_result.get("gaps", [])
        st.metric("Skill Gaps", len(gaps))

    with col_m4:
        requirements = mapping_result.get("matched_requirements", [])
        st.metric("Met Requirements", len(requirements))

    st.markdown("---")

    if st.session_state.step == 3:
        render_cv_comparison(enhance_data)
    else:
        render_feedback_display(enhance_data)

    st.markdown("---")

    render_download_section(
        enhance_data,
        match_score,
        allow_export=(st.session_state.step == 3),
    )


def render_download_section(enhance_data, match_score, allow_export=True):
    st.markdown(
        """
        <style>
        /* PDF button */
        div[data-testid="stDownloadButton"] button[kind="primary"] {
            background-color: #ffffff !important;
            color: #0b63ce !important;
            border: 1px solid #d1d5db !important;
        }

        /* DOCX button */
        div[data-testid="stDownloadButton"] button[kind="secondary"] {
            background-color: #e6f3ff !important;
            color: #0b63ce !important;
            border: 1px solid #e6f3ff !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"### {ICONS['download']} Download Your CV",
        unsafe_allow_html=True,
    )

    col_pdf, col_docx = st.columns(2)

    enhanced_resume = enhance_data.get("enhanced_resume", {}) if allow_export else {}

    personal_info = enhanced_resume.get("personal_info", {}) if enhanced_resume else {}
    full_name = personal_info.get("full_name") or "personalized_cv"
    safe_slug = "".join(
        ch for ch in full_name.lower().replace(" ", "_")
        if ch.isalnum() or ch == "_"
    )
    base_filename = f"{safe_slug}_resume"

    with col_pdf:
        if allow_export:
            if enhanced_resume:
                try:
                    api_client = ResumeEnhancerAPI()
                    pdf_bytes = api_client.export_resume(
                        enhanced_resume, file_type="pdf"
                    )
                    if pdf_bytes:
                        st.download_button(
                            "Download Personalized CV (PDF)",
                            data=pdf_bytes,
                            file_name=f"{base_filename}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            type="primary",
                        )
                    else:
                        st.warning("PDF generation failed. Please contact support.")
                except Exception as e:
                    st.error(f"Failed to generate PDF: {e}")
            else:
                st.warning("Enhanced resume data not available for PDF export")
        else:
            st.info("Low match – consider improving skills or targeting other roles")

    with col_docx:
        if allow_export:
            if enhanced_resume:
                try:
                    api_client = ResumeEnhancerAPI()
                    docx_bytes = api_client.export_resume(
                        enhanced_resume, file_type="docx"
                    )
                    if docx_bytes:
                        st.download_button(
                            "Download Personalized CV (DOCX)",
                            data=docx_bytes,
                            file_name=f"{base_filename}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                            type="secondary",
                        )
                    else:
                        st.warning("DOCX generation failed. Please contact support.")
                except Exception as e:
                    st.error(f"Failed to generate DOCX: {e}")
            else:
                st.warning("Enhanced resume data not available for DOCX export")

    st.markdown("")

    if st.button("New CV", use_container_width=True, type="secondary"):
        reset_app()
        st.rerun()
