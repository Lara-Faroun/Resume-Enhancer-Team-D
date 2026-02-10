import streamlit as st
from assets.icons import ICONS
from utils import validate_file, validate_job_description, format_file_size, reset_app


def render_upload_section():
    st.markdown(
        """
        <style>
        /* Make the CV upload area height comparable to the JD text area */
        div.stFileUploader {
            min-height: 200px;
        }

        /* Make the uploaded file success badge blue with white text */
        .success-badge {
            background-color: #0b63ce;
            color: #ffffff;
            border-radius: 6px;
            padding: 0.5rem 0.75rem;
            font-weight: 600;
        }

        /* Inline error row that supports SVG */
        .error-row{
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
            border-radius: 8px;
            padding: .6rem .75rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: .5rem;
            margin-top: .5rem;
        }
   
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("""
        <div class="step-card">
            <div class="step-header">
                <div class="step-number">1</div>
                <div class="step-title">Upload Your CV & Job Description</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown(f"#### {ICONS['attachment']} Your CV", unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload PDF or DOCX",
            type=["pdf", "docx"],
            help="Accepted types: PDF or DOCX (max 10MB)",
            label_visibility="collapsed",
            key=f"cv_file_uploader_{st.session_state.widget_key}",
        )

        if uploaded_file:
            is_valid, msg = validate_file(uploaded_file)
            if is_valid:
                st.markdown(
                    f"""
                    <div class="success-badge">
                        {uploaded_file.name} ({format_file_size(uploaded_file.size)})
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.session_state.uploaded_file = uploaded_file
            else:
                st.markdown(
                    f"""<div class="error-row">{ICONS['x_circle']} {msg}</div>""",
                    unsafe_allow_html=True,
                )
                st.session_state.uploaded_file = None

    with col2:
        st.markdown(f"#### {ICONS['clipboard']} Job Description", unsafe_allow_html=True)

        job_description = st.text_area(
            "Paste the complete job posting",
            height=200,
            placeholder=(
                "Paste the job description here...\n\n"
                "Include:\n"
                "• Job title and responsibilities\n"
                "• Required skills and qualifications\n"
                "• Experience requirements"
            ),
            label_visibility="collapsed",
            key=f"job_desc_input_{st.session_state.widget_key}",
        )

        if job_description:
            char_count = len(job_description.strip())
            color = "green" if char_count >= 100 else "orange"
            st.caption(f":{color}[{char_count} characters]")

        st.session_state.job_description = job_description

    st.markdown(f"{ICONS['check']} Consent", unsafe_allow_html=True)
    consent = st.checkbox(
        "I confirm I have permission to use this CV and the data will be processed securely",
        help="Required for processing",
        key=f"consent_check_{st.session_state.widget_key}",
    )

    st.markdown("")

 
    col_btn1, col_btn2 = st.columns([2, 2])

    with col_btn1:
        is_valid_file, _ = validate_file(st.session_state.uploaded_file)
        is_valid_jd, _ = validate_job_description(job_description)

        can_submit = is_valid_file and is_valid_jd and consent

        if st.button(
            "Generate Personalized CV",
            disabled=not can_submit,
            use_container_width=True,
            type="primary",
            key="btn_generate"
        ):
            st.session_state.step = 2
            st.rerun()


       

    with col_btn2:
        if st.button(
            "Clear Form",
            use_container_width=True,
            type="secondary",
            key="btn_clear"
        ):
            reset_app()
            st.rerun()
