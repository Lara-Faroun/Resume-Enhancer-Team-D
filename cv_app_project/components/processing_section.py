import json
import streamlit as st
import requests
from services import ResumeEnhancerAPI
from config import AppConfig

# Progress model: 0-100 scale, converted to 0-1 for Streamlit
PROGRESS_AFTER_PARSE = AppConfig.PROGRESS_AFTER_PARSE
PROGRESS_MAPPING_START = AppConfig.PROGRESS_MAPPING_START
PROGRESS_AFTER_MAPPING = AppConfig.PROGRESS_AFTER_MAPPING
PROGRESS_SECTIONS_START = AppConfig.PROGRESS_SECTIONS_START
PROGRESS_SECTIONS_END = AppConfig.PROGRESS_SECTIONS_END
PROGRESS_COMPLETE = AppConfig.PROGRESS_COMPLETE


def _progress_fraction(percent_0_100: float) -> float:
    """Clamp percent to [0, 100] and return fraction in [0, 1] for st.progress()."""
    return min(100, max(0, percent_0_100)) / 100


def render_processing_section():
    st.markdown("""
        <div class="step-card">
            <div class="step-header">
                <div class="step-number">2</div>
                <div class="step-title">AI Processing</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if not st.session_state.processing:
        # If we have results but landed here (e.g. after rerun), go straight to results — no extra button.
        if st.session_state.get("enhance_result"):
            status = st.session_state.enhance_result.get("status", "complete")
            st.session_state.step = 3 if status == "complete" else 4
            st.rerun()
            return
        st.info("✨ Ready to process your CV with AI")
        if st.button("▶️ Start Processing", use_container_width=True, type="primary"):
            st.session_state.processing = True
            st.rerun()
        return

    if st.session_state.processing:
        progress_bar = st.progress(_progress_fraction(0))
        status_text = st.empty()
        
        st.markdown("---")
        st.markdown("### 🔄 Live Progress")
        
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
            status_text.info("📤 Uploading and parsing CV...")
            
            parse_result = api_client.parse_resume(
                st.session_state.uploaded_file,
                st.session_state.job_description
            )
            st.session_state.parse_result = parse_result
            
            progress_bar.progress(_progress_fraction(PROGRESS_AFTER_PARSE))
            status_text.info("🤖 Starting AI enhancement (streaming mode)...")
            
            accumulated_result = {}
            section_containers = {}
            display_pct = PROGRESS_AFTER_PARSE

            for event in api_client.enhance_resume_streaming(
                parse_result['resume'],
                parse_result['job_description']
            ):
                event_type = event.get('event_type', '')
                progress_percent = event.get('progress_percent', 0)

                if event_type == 'mapping_start':
                    status_text.info("🔍 Analyzing CV and job description...")
                    stage_display.info("🔍 Mapping")
                    display_pct = PROGRESS_MAPPING_START
                    progress_bar.progress(_progress_fraction(display_pct))

                elif event_type == 'mapping_complete':
                    match_score = event.get('match_score', 0)
                    accumulated_result['mapping_result'] = {
                        'match_score': match_score,
                        'matched_skills': [],
                        'gaps': [],
                        'matched_requirements': []
                    }
                    # Backend sends match_score 0-10; display as 0-100% via * 10. Low match = red container.
                    score_pct = int(match_score * 10)
                    if match_score >= AppConfig.MIN_MATCH_SCORE:
                        stage_display.success(f"✅ Match: {score_pct}%")
                    else:
                        stage_display.error(f"⚠️ Match: {score_pct}%")
                    display_pct = PROGRESS_AFTER_MAPPING
                    progress_bar.progress(_progress_fraction(display_pct))

                elif event_type == 'section_start':
                    section = event.get('section', '')
                    section_icon = {
                        'summary': '📝',
                        'experiences': '💼',
                        'educations': '🎓',
                        'skills': '⚡',
                        'certifications': '🏆',
                        'languages': '🌐',
                        'projects': '🚀'
                    }.get(section, '📄')
                    section_title = section.replace('_', ' ').title()
                    status_text.info(f"{section_icon} Enhancing {section_title}...")
                    stage_display.info(f"{section_icon} {section_title}")
                    with sections_container:
                        st.markdown(f"#### {section_icon} {section_title}")
                        section_containers[section] = st.empty()
                    display_pct = PROGRESS_SECTIONS_START + (progress_percent / 100) * (PROGRESS_SECTIONS_END - PROGRESS_SECTIONS_START)
                    display_pct = min(PROGRESS_SECTIONS_END, max(PROGRESS_SECTIONS_START, display_pct))
                    progress_bar.progress(_progress_fraction(display_pct))

                elif event_type == 'section_delta':
                    section = event.get('section', '')
                    accumulated_text = event.get('accumulated_text', '')
                    if section in section_containers and accumulated_text:
                        with section_containers[section]:
                            st.markdown(accumulated_text)
                    display_pct = PROGRESS_SECTIONS_START + (progress_percent / 100) * (PROGRESS_SECTIONS_END - PROGRESS_SECTIONS_START)
                    display_pct = min(PROGRESS_SECTIONS_END, max(PROGRESS_SECTIONS_START, display_pct))
                    progress_bar.progress(_progress_fraction(display_pct))

                elif event_type == 'section_complete':
                    section = event.get('section', '')
                    partial_payload = event.get('partial_payload', {})
                    if section in partial_payload:
                        section_data = partial_payload[section]
                        enhanced_text = section_data.get('enhanced', '')
                        if section in section_containers and enhanced_text:
                            with section_containers[section]:
                                st.success("✅ Complete")
                                with st.expander("View Full Content"):
                                    st.markdown(enhanced_text)
                    
                    display_pct = PROGRESS_SECTIONS_START + (progress_percent / 100) * (PROGRESS_SECTIONS_END - PROGRESS_SECTIONS_START)
                    display_pct = min(PROGRESS_SECTIONS_END, max(PROGRESS_SECTIONS_START, display_pct))
                    progress_bar.progress(_progress_fraction(display_pct))

                elif event_type == 'complete':
                    state = event.get('state', {})
                    status = event.get('status', 'complete')
                    accumulated_result = {
                        "status": status,
                        "mapping_result": state.get("mapping_result", {}),
                        "enhanced_resume": state.get("enhanced_resume", {}),
                        "report_summary": state.get("report_summary", ""),
                        "feedback_message": state.get("feedback_message", ""),
                    }
                    st.session_state.enhance_result = accumulated_result

                    display_pct = PROGRESS_COMPLETE
                    progress_bar.progress(_progress_fraction(display_pct))
                    progress_display.metric("📊 Progress", f"{display_pct:.1f}%")
                    stage_display.success("✅ Complete")
                    break

                elif event_type == 'error':
                    error_msg = event.get('message', 'Unknown error')
                    raise Exception(error_msg)

                progress_display.metric("📊 Progress", f"{display_pct:.1f}%")
            
            st.session_state.processing = False
            st.markdown("---")
            if st.button("Final step", use_container_width=True, type="primary"):
                status = st.session_state.enhance_result.get("status", "complete")
                st.session_state.step = 3 if status == "complete" else 4
                st.rerun()

        except requests.Timeout:
            progress_bar.progress(_progress_fraction(PROGRESS_COMPLETE))
            st.session_state.error = f"Request timed out after {AppConfig.API_TIMEOUT} seconds"
            st.session_state.processing = False
            status_text.error("❌ Request timed out")
            
        except requests.RequestException as e:
            progress_bar.progress(_progress_fraction(PROGRESS_COMPLETE))
            st.session_state.error = f"API Error: {str(e)}"
            st.session_state.processing = False
            status_text.error(f"❌ Failed to connect to backend: {str(e)}")
        
        except Exception as e:
            progress_bar.progress(_progress_fraction(PROGRESS_COMPLETE))
            st.session_state.error = str(e)
            st.session_state.processing = False
            status_text.error(f"❌ Error: {str(e)}")
    
    if st.session_state.error:
        st.error(f"**Error:** {st.session_state.error}")
        with st.expander("🔍 Troubleshooting Help"):
            st.markdown(f"""
            **Common Solutions:**
            - Ensure backend is running at `{AppConfig.API_BASE_URL}`
            - Check that CV file is valid
            - Verify job description format
            - Check backend logs for details
            - Make sure streaming mode is enabled
            
            **API Endpoints:**
            - Health: `{AppConfig.API_BASE_URL}/health`
            - Parse: `{AppConfig.API_BASE_URL}{AppConfig.API_PARSE_ENDPOINT}`
            - Enhance (Streaming): `{AppConfig.API_BASE_URL}{AppConfig.API_ENHANCE_ENDPOINT}?mode=incremental`
            """)
        
        if st.button("🔄 Try Again", use_container_width=True):
            st.session_state.error = None
            st.session_state.processing = False
            st.session_state.step = 1
            st.rerun()