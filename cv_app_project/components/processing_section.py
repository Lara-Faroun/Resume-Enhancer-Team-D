import streamlit as st
import requests
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
        progress = st.progress(0)
        status = st.empty()
        
        try:
            api_client = ResumeEnhancerAPI()
            
            progress.progress(10)
            status.info("📤 Uploading CV and parsing...")
            
            parse_result = api_client.parse_resume(
                st.session_state.uploaded_file,
                st.session_state.job_description
            )
            
            st.session_state.parse_result = parse_result
            
            progress.progress(40)
            status.info("🤖 AI is analyzing and personalizing your CV...")
            
            enhance_result = api_client.enhance_resume(
                parse_result['resume'],
                parse_result['job_description']
            )
            
            st.session_state.enhance_result = enhance_result
            
            progress.progress(90)
            status.info("📝 Formatting results...")
            
            st.session_state.step = 3
            
            progress.progress(100)
            status.success("✅ Your personalized CV is ready!")
            st.balloons()
            
            st.session_state.processing = False
            st.rerun()
            
        except requests.Timeout:
            progress.progress(100)
            st.session_state.error = f"Request timed out after {AppConfig.API_TIMEOUT} seconds. Please try again."
            st.session_state.processing = False
            status.error("❌ Request timed out")
            
        except requests.RequestException as e:
            progress.progress(100)
            st.session_state.error = f"API Error: {str(e)}"
            st.session_state.processing = False
            status.error(f"❌ Failed to connect to backend: {str(e)}")
        
        except Exception as e:
            progress.progress(100)
            st.session_state.error = str(e)
            st.session_state.processing = False
            status.error(f"❌ Processing error: {str(e)}")
    
    if st.session_state.error:
        st.error(f"**Error:** {st.session_state.error}")
        with st.expander("🔍 Troubleshooting Help"):
            st.markdown(f"""
            **Common Solutions:**
            - Ensure your backend is running at `{AppConfig.API_BASE_URL}`
            - Check that the CV file is valid and not corrupted
            - Verify the job description is properly formatted
            - Check backend logs for detailed error messages
            - Make sure all required backend dependencies are installed
            
            **API Endpoints:**
            - Health Check: `{AppConfig.API_BASE_URL}/health`
            - Parse: `{AppConfig.API_BASE_URL}{AppConfig.API_PARSE_ENDPOINT}`
            - Enhance: `{AppConfig.API_BASE_URL}{AppConfig.API_ENHANCE_ENDPOINT}`
            """)
        
        if st.button("🔄 Try Again", use_container_width=True):
            st.session_state.error = None
            st.session_state.processing = False
            st.session_state.step = 1
            st.rerun()
