import streamlit as st
from config.settings import AppConfig
from components.header import render_header
from components.upload_section import render_upload_section
from components.processing_section import render_processing_section
from components.results_section import render_results_section
from utils.session_state import init_session_state
from assets.styles import apply_custom_css

st.set_page_config(
    page_title=AppConfig.APP_TITLE,
    page_icon=AppConfig.APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_custom_css()
init_session_state()

render_header()

if st.session_state.step == 1:
    render_upload_section()
elif st.session_state.step == 2:
    render_processing_section()
elif st.session_state.step == 3:
    render_results_section()

st.markdown("---")
st.markdown(
    f"<p style='text-align: center; color: #6b7280; font-size: 0.9rem;'>{AppConfig.FOOTER_TEXT}</p>",
    unsafe_allow_html=True
)
