import streamlit as st
from assets.icons import ICONS


def format_resume_as_html(resume_data: dict) -> str:
    html_parts = []

    personal_info = resume_data.get("personal_info", {})
    if personal_info.get("full_name"):
        html_parts.append(f"<h1>{personal_info['full_name']}</h1>")
        contact = []
        if personal_info.get("email_address"):
            contact.append(personal_info["email_address"])
        if personal_info.get("phone_number"):
            contact.append(personal_info["phone_number"])
        if contact:
            html_parts.append(f"<p>{' | '.join(contact)}</p>")

    if resume_data.get("summary"):
        html_parts.append("<h2>Professional Summary</h2>")
        html_parts.append(f"<p>{resume_data['summary']}</p>")

    experiences = resume_data.get("experiences", [])
    if experiences:
        html_parts.append("<h2>Work Experience</h2>")
        for exp in experiences:
            html_parts.append(
                f"<h3>{exp.get('role_title', '')} - {exp.get('company_name', '')}</h3>"
            )
            html_parts.append(
                f"<p><em>{exp.get('start_date', '')} - {exp.get('end_date', 'Present')}</em></p>"
            )
            if exp.get("description"):
                html_parts.append("<ul>")
                for desc in exp["description"]:
                    html_parts.append(f"<li>{desc}</li>")
                html_parts.append("</ul>")

    educations = resume_data.get("educations", [])
    if educations:
        html_parts.append("<h2>Education</h2>")
        for edu in educations:
            html_parts.append(
                f"<h3>{edu.get('degree', '')} in {edu.get('major', '')}</h3>"
            )
            html_parts.append(f"<p>{edu.get('university_name', '')}</p>")
            if edu.get("start_date") or edu.get("end_date"):
                html_parts.append(
                    f"<p><em>{edu.get('start_date', '')} - {edu.get('end_date', '')}</em></p>"
                )

    skills = resume_data.get("skills", [])
    if skills:
        html_parts.append("<h2>Skills</h2>")
        html_parts.append("<ul>")
        for skill in skills:
            skill_name = skill.get("skill_name", "")
            skill_type = skill.get("skill_type", "")
            html_parts.append(
                f"<li>{skill_name}"
                + (f" ({skill_type})" if skill_type else "")
                + "</li>"
            )
        html_parts.append("</ul>")

    certifications = resume_data.get("certifications", [])
    if certifications:
        html_parts.append("<h2>Certifications</h2>")
        html_parts.append("<ul>")
        for cert in certifications:
            cert_text = cert.get("certification_name", "")
            if cert.get("issuing_organization"):
                cert_text += f" - {cert['issuing_organization']}"
            html_parts.append(f"<li>{cert_text}</li>")
        html_parts.append("</ul>")

    projects = resume_data.get("projects", [])
    if projects:
        html_parts.append("<h2>Projects</h2>")
        for proj in projects:
            html_parts.append(f"<h3>{proj.get('project_name', '')}</h3>")
            if proj.get("description"):
                html_parts.append("<ul>")
                for desc in proj["description"]:
                    html_parts.append(f"<li>{desc}</li>")
                html_parts.append("</ul>")

    languages = resume_data.get("languages", [])
    if languages:
        html_parts.append("<h2>Languages</h2>")
        html_parts.append("<ul>")
        for lang in languages:
            html_parts.append(
                f"<li>{lang.get('language', '')} - {lang.get('proficiency_level', '')}</li>"
            )
        html_parts.append("</ul>")

    return "\n".join(html_parts)


def render_cv_comparison(enhance_data):
    st.markdown(
        """
        <style>
        .change-report-box {
            max-height: 650px;
            overflow-y: auto;
        }

        .cv-container.personalized {
            max-height: 650px;
            overflow-y: auto;
        }

        .skill-badge-group {
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            margin-bottom: 0.5rem;
        }

        .skill-badge {
            display: inline-block;
            padding: 0.25rem 0.6rem;
            border-radius: 9999px;
            background-color: #ffffff !important;
            border: 1px solid #d1d5db;
            font-size: 14.5px;
            line-height: 1.25rem;
        }

        .skill-badge.matched {
            border-color: #16a34a;
            color: #166534;
        }

        .skill-badge.missing {
            border-color: #dc2626;
            color: #991b1b;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="comparison-badge">{ICONS["note"]} Personalized CV Preview</div>',
        unsafe_allow_html=True,
    )

    enhanced_resume = enhance_data.get("enhanced_resume", {})
    if not enhanced_resume:
        st.warning("Enhanced resume not available")
        return

    report_summary = enhance_data.get("report_summary", "")

    col_cv, col_report = st.columns([2, 1], gap="medium")

    with col_cv:
        enhanced_html = format_resume_as_html(enhanced_resume)
        st.markdown(
            f"""
            <div class="cv-container personalized">
                {enhanced_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_report:
        st.markdown(
            f"#### {ICONS['note']} Change Report",
            unsafe_allow_html=True,
        )
        if report_summary:
            st.markdown(
                f"""
                <div class="change-report-box">
                    <p>{report_summary}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("No change report data available.")

    st.markdown("---")
    st.markdown(
        f"### {ICONS['chart']} Personalization Summary",
        unsafe_allow_html=True,
    )

    mapping_result = enhance_data.get("mapping_result", {})

    col_skills1, col_skills2 = st.columns(2)

    with col_skills1:
        st.markdown(
            f"#### {ICONS['check_circle']} Matched Skills",
            unsafe_allow_html=True,
        )
        matched_skills = mapping_result.get("matched_skills", [])
        if matched_skills:
            badges_html = "".join(
                f'<span class="skill-badge matched">{skill}</span>'
                for skill in matched_skills
            )
            st.markdown(
                f'<div class="skill-badge-group">{badges_html}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("No matched skills data available")

    with col_skills2:
        st.markdown(
            f"#### {ICONS['alert']} Skill Gaps",
            unsafe_allow_html=True,
        )
        gaps = mapping_result.get("gaps", [])
        if gaps:
            badges_html = "".join(
                f'<span class="skill-badge missing">{gap}</span>'
                for gap in gaps
            )
            st.markdown(
                f'<div class="skill-badge-group">{badges_html}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.success("No major skill gaps identified!")
