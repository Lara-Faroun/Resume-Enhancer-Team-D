import streamlit as st
from assets.icons import ICONS


def render_feedback_display(enhance_data):
    st.markdown(
        """
        <style>
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

    mapping_result = enhance_data.get("mapping_result", {})
    match_score = mapping_result.get("match_score", 0)
    feedback_message = enhance_data.get(
        "feedback_message",
        "Your CV does not align well with this job description.",
    )

    score_pct = int(match_score * 10)

    st.markdown(
        f"""
        <div class="feedback-card" style="background-color: #f3f4f6;">
            <div class="feedback-title">
                {ICONS['alert']} Low Match Score: {score_pct}%
            </div>
            <div class="feedback-content">
                <p><strong>Your CV doesn't align well with this job description.</strong></p>
                <h3>{ICONS['lightning']} Our Recommendations</h3>
                <p>{feedback_message}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"<h3>{ICONS['check_circle']} What You Have</h3>",
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
            st.markdown(
                "<p><em>There are no matched skills</em></p>",
                unsafe_allow_html=True,
            )

    with col2:
        st.markdown(
            f"<h3>{ICONS['x_circle']} What You’re Missing</h3>",
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
            st.markdown(
                "<p><em>No specific gaps identified</em></p>",
                unsafe_allow_html=True,
            )
