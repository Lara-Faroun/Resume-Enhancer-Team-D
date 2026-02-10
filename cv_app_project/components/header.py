import streamlit as st
from assets.icons import ICONS   

def render_header():
    st.markdown(f"""
        <div class="hero-section">
            <div class="hero-title  ">
                {ICONS['robot']} AI CV Personalization Engine
            </div>
            <div class="hero-subtitle">
                Transform your CV to perfectly match any job description in seconds
            </div>
        </div>
    """, unsafe_allow_html=True)
