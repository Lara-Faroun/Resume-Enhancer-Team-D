import streamlit as st

def init_session_state():
    defaults = {
        "step": 1,
        "uploaded_file": None,
        "job_description": "",
        "parse_result": None,
        "enhance_result": None,
        "processing": False,
        "error": None,
        "widget_key": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_app():
    st.session_state.step = 1
    st.session_state.uploaded_file = None
    st.session_state.job_description = ""
    st.session_state.parse_result = None
    st.session_state.enhance_result = None
    st.session_state.processing = False
    st.session_state.error = None
    st.session_state.widget_key += 1
