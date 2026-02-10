import streamlit as st

def apply_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap');
        
        * {
            font-family: 'Inter', sans-serif;
        }
          /* SVG icons */
        .icon{
          width: 1.1em;
          height: 1.1em;
          stroke-width: 2;
          font-size: 1.5em;    
          vertical-align: -0.15em;
          margin-right: .4em;
          display: inline-block;
         }
        .icon *{ stroke: #7655ae; }
             
     .icon-spinner { 
        color: #22c55e !important; 
        }

        .icon-spin * {
        stroke: currentColor !important;
        stroke-width: 3 !important;
        opacity: 1 !important;
        }

        
        .icon-spin {
        font-size: 1.6em !important;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stSidebar"] {display: none;}
        
        .main {
            padding: 1.5rem 3rem;
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .hero-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2.5rem 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            text-align: center;
            color: white;
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .hero-section::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 15s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.1); opacity: 0.3; }
        }
        
        .hero-title {
            font-size: 2.8rem;
            font-weight: 900;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.2);
            position: relative;
            z-index: 1;
        }
        .hero-title .icon{
            width: 1.2em;
            height: 1.2em;
            margin-right: .01em;
            vertical-align: -0.18em;
 
        }
        .hero-title * {
            stroke: #ffffff !important;
            }

        .hero-subtitle {
            font-size: 1.15rem;
            opacity: 0.95;
            font-weight: 400;
            position: relative;
            z-index: 1;
        }
        
        .step-card {
            background: white;
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
            border: 1px solid #e5e7eb;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
        }
        
        .step-card:hover {
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }
        
        .step-header {
            display: flex;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #f3f4f6;
        }
        
        .step-number {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.3rem;
            margin-right: 1rem;
            box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
        }
        
        .step-title {
            font-size: 1.6rem;
            font-weight: 700;
            color: #1f2937;
        }
        
        .success-badge {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            display: inline-block;
            font-weight: 600;
            margin: 0.5rem 0;
            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
        }
        
        .stButton > button {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            padding: 0.75rem 2rem;
            border-radius: 12px;
            border: none;
            font-size: 1.05rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        /* upload file */
        button[data-testid="stBaseButton-primary"]  {
        color: #ffffff !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 2.5rem;
            font-weight: 700;
            color: #667eea;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.95rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stProgress > div > div {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 8px;
            border-radius: 4px;
        }
        
        .cv-container {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            border: 2px solid #e5e7eb;
            height: 650px;
            overflow-y: auto;
            position: relative;
        }
        
        .cv-container.original {
            border-top: 4px solid #9ca3af;
        }
        
        .cv-container.personalized {
            border-top: 4px solid #667eea;
            background: linear-gradient(to bottom, #f9fafb 0%, #ffffff 100%);
        }
        
        .cv-label {
            position: sticky;
            top: 0;
            background: white;
            padding: 0.75rem 1rem;
            margin: -2rem -2rem 1rem -2rem;
            font-weight: 700;
            font-size: 1.1rem;
            border-bottom: 2px solid #e5e7eb;
            z-index: 10;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .cv-label.original {
            background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
            color: #374151;
        }
        
        .cv-label.personalized {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .feedback-card {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-left: 5px solid #f59e0b;
            padding: 2.5rem;
            border-radius: 16px;
            margin: 2rem 0;
            box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
        }
        
        .feedback-title {
            font-size: 2rem;
            font-weight: 700;
            color: #92400e;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .feedback-content {
            color: #78350f;
            font-size: 1.1rem;
            line-height: 1.8;
        }
        
        .feedback-section {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin-top: 1.5rem;
            border-left: 4px solid #f59e0b;
        }
        
        .skill-badge {
            display: inline-block;
            padding: 0.4rem 0.9rem;
            margin: 0.3rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        .skill-badge.matched {
            background: #d1fae5;
            color: #065f46;
            border: 2px solid #10b981;
        }
        
        .skill-badge.missing {
            background: #fee2e2;
            color: #991b1b;
            border: 2px solid #ef4444;
        }
        
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            border-radius: 10px;
            border: 2px solid #e5e7eb;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        }
        
        [data-testid="stFileUploader"] {
            padding: 1.5rem;
            background: #f9fafb;
            border-radius: 12px;
            border: 2px dashed #d1d5db;
            transition: all 0.3s ease;
        }
        
        [data-testid="stFileUploader"]:hover {
            border-color: #667eea;
            background: #f0f1ff;
            border-style: solid;
        }
        
        .cv-container::-webkit-scrollbar {
            width: 10px;
        }
        
        .cv-container::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }
        
        .cv-container::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }
        
        .cv-container::-webkit-scrollbar-thumb:hover {
            background: #5568d3;
        }
        
        hr {
            margin: 2rem 0;
            border: none;
            border-top: 2px solid #e5e7eb;
        }
        
        .comparison-badge {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            padding: 0.5rem 1.2rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
        }
        /* animate Icons */ 
            @keyframes icon-spin {
            from { transform: rotate(0deg); }
            to   { transform: rotate(360deg); }
            }

            @keyframes icon-pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50%      { transform: scale(1.08); opacity: 0.7; }
            }


            .icon-spin {
            animation: icon-spin 0.9s linear infinite;
            transform-origin: 50% 50%;
            display: inline-block;
            }

            .icon-pulse {
            animation: icon-pulse 1.1s ease-in-out infinite;
            transform-origin: 50% 50%;
            display: inline-block;
            }

            /* Bar */
            [data-testid="stProgress"] > div > div {
            background: linear-gradient(
                270deg,
                #22c55e,
                #4ade80,
                #86efac,
                #22c55e
            );
            background-size: 400% 400%;
            animation: greenFlow 3s ease infinite;
        }

        @keyframes greenFlow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .progress-success [data-testid="stProgress"] > div > div {
        background: linear-gradient(90deg, #16a34a, #4ade80) !important;
        }
        .progress-error [data-testid="stProgress"] > div > div {
            background: linear-gradient(90deg, #dc2626, #f87171) !important;
        }



        </style>
    """, unsafe_allow_html=True)
