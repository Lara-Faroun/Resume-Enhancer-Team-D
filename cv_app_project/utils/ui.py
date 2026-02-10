import streamlit as st
from assets.icons import ICONS


def h(text: str, icon: str, level: int = 4):
   
    level = max(1, min(level, 6))
    hashes = "#" * level
    st.markdown(
        f"{hashes} {ICONS[icon]} {text}",
        unsafe_allow_html=True
    )


def label(text: str, icon: str):
  
    st.markdown(
        f"{ICONS[icon]} {text}",
        unsafe_allow_html=True
    )


def status(text: str, state: str):
 
    icon_map = {
        "success": "check_circle",
        "error": "x_circle",
        "warning": "lightning",
    }

    icon = icon_map.get(state, "check")
    st.markdown(
        f"{ICONS[icon]} **{text}**",
        unsafe_allow_html=True
    )
