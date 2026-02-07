import streamlit as st
import requests
import time
from services import ResumeEnhancerAPI
from config import AppConfig

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
        st.info("✨ Ready to process your CV with AI")
        
        if st.button("▶️ Start Processing", use_container_width=True, type="primary"):
            st.session_state.processing = True
            st.rerun()
    
    if st.session_state.processing:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        st.markdown("---")
        st.markdown("### 🔄 Live Progress")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            time_display = st.empty()
        with col2:
            progress_display = st.empty()
        with col3:
            stage_display = st.empty()
        
        st.markdown("---")
        
        sections_container = st.container()
        
        try:
            api_client = ResumeEnhancerAPI()
            
            progress_bar.progress(10)
            status_text.info("📤 Uploading and parsing CV...")
            
            parse_result = api_client.parse_resume(
                st.session_state.uploaded_file,
                st.session_state.job_description
            )
            st.session_state.parse_result = parse_result
            
            progress_bar.progress(20)
            status_text.info("🤖 Starting AI enhancement (streaming mode)...")
            
            accumulated_result = {}
            section_containers = {}
            start_time = time.time()
            
            for event in api_client.enhance_resume_streaming(
                parse_result['resume'],
                parse_result['job_description']
            ):
                event_type = event.get('event_type', '')
                
                elapsed_ms = event.get('elapsed_ms', 0)
                progress_percent = event.get('progress_percent', 0)
                
                elapsed_sec = elapsed_ms / 1000 if elapsed_ms else (time.time() - start_time)
                time_display.metric("⏱️ Time", f"{elapsed_sec:.1f}s")
                progress_display.metric("📊 Progress", f"{progress_percent:.1f}%")
                
                if event_type == 'mapping_start':
                    status_text.info("🔍 Analyzing CV and job description...")
                    stage_display.info("🔍 Mapping")
                    progress_bar.progress(20)
                
                elif event_type == 'mapping_complete':
                    match_score = event.get('match_score', 0)
                    accumulated_result['mapping_result'] = {
                        'match_score': match_score * 10,
                        'matched_skills': [],
                        'gaps': [],
                        'matched_requirements': []
                    }
                    status_text.success(f"✅ Skill mapping complete! Match: {int(match_score * 100)}%")
                    stage_display.success(f"✅ Match: {int(match_score * 100)}%")
                    progress_bar.progress(30)
                
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
                    
                    progress_value = 30 + (progress_percent * 0.6)
                    progress_bar.progress(min(int(progress_value), 95) / 100)
                
                elif event_type == 'section_delta':
                    section = event.get('section', '')
                    accumulated_text = event.get('accumulated_text', '')
                    
                    if section in section_containers and accumulated_text:
                        with section_containers[section]:
                            st.markdown(accumulated_text)
                    
                    progress_value = 30 + (progress_percent * 0.6)
                    progress_bar.progress(min(int(progress_value), 95) / 100)
                
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
                    
                    status_text.success(f"✅ {section.title()} completed")
                    progress_value = 30 + (progress_percent * 0.6)
                    progress_bar.progress(min(int(progress_value), 95) / 100)
                
                elif event_type == 'complete':
                    state = event.get('state', {})
                    
                    accumulated_result['enhanced_resume'] = state.get('enhanced_resume', {})
                    accumulated_result['mapping_result'] = state.get('mapping_result', {})
                    accumulated_result['change_report'] = []
                    
                    mapping = state.get('mapping_result', {})
                    if mapping:
                        accumulated_result['mapping_result'] = {
                            'match_score': mapping.get('match_score', 0) * 10,
                            'matched_skills': mapping.get('matched_skills', []),
                            'gaps': mapping.get('gaps', []),
                            'matched_requirements': mapping.get('matched_requirements', [])
                        }
                    
                    report_summary = state.get('report_summary', '')
                    if report_summary:
                        accumulated_result['feedback_message'] = report_summary
                    
                    st.session_state.enhance_result = accumulated_result
                    
                    progress_bar.progress(100)
                    status_text.success("✅ Your personalized CV is ready!")
                    stage_display.success("✅ Complete")
                    st.balloons()
                    
                    break
                
                elif event_type == 'error':
                    error_msg = event.get('message', 'Unknown error')
                    raise Exception(error_msg)
            
            st.session_state.step = 3
            st.session_state.processing = False
            
            time.sleep(1)
            st.rerun()
            
        except requests.Timeout:
            progress_bar.progress(100)
            st.session_state.error = f"Request timed out after {AppConfig.API_TIMEOUT} seconds"
            st.session_state.processing = False
            status_text.error("❌ Request timed out")
            
        except requests.RequestException as e:
            progress_bar.progress(100)
            st.session_state.error = f"API Error: {str(e)}"
            st.session_state.processing = False
            status_text.error(f"❌ Failed to connect to backend: {str(e)}")
        
        except Exception as e:
            progress_bar.progress(100)
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