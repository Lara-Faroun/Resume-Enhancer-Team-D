import streamlit as st

def render_header():
    st.markdown("""
        <div class="hero-section">
            <div class="hero-title">🎯 AI CV Personalization Engine</div>
            <div class="hero-subtitle">Transform your CV to perfectly match any job description in seconds</div>
        </div>
    """, unsafe_allow_html=True)
