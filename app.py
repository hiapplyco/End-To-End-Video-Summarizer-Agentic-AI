import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
import google.generativeai as genai
from google.generativeai import upload_file, get_file

import time
import os
import tempfile
from pathlib import Path

def show_toast(message, duration=3000):
    """Display a toast-like notification using injected JavaScript."""
    st.markdown(f"""
    <script>
    var toast = document.createElement('div');
    toast.innerHTML = "{message}";
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.backgroundColor = '#e74c3c';
    toast.style.color = 'white';
    toast.style.padding = '10px';
    toast.style.borderRadius = '5px';
    toast.style.zIndex = '1000';
    document.body.appendChild(toast);
    setTimeout(function(){{ document.body.removeChild(toast); }}, {duration});
    </script>
    """, unsafe_allow_html=True)

# Retrieve API key from secrets and set it as an environment variable
API_KEY = st.secrets["google"]["api_key"]
if API_KEY:
    os.environ["GOOGLE_API_KEY"] = API_KEY  # Make sure dependent libraries can find it
    genai.configure(api_key=API_KEY)
else:
    st.error("Google API Key not found. Please set the GOOGLE_API_KEY in Streamlit secrets.")
    st.stop()

st.set_page_config(
    page_title="Multimodal AI Agent - BJJ Video Analyzer",
    page_icon="🥋",
    layout="wide"
)

st.markdown("""
    <style>
    /* Base header styling */
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        color: #2C3E50;
        margin-bottom: 0px;
        text-align: center;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #7F8C8D;
        margin-bottom: 30px;
        text-align: center;
    }
    /* Inputs and buttons: default max width and centering */
    .stTextArea textarea, .stButton button, .stFileUploader, video {
        max-width: 480px;
        width: 100%;
        margin: 0 auto;
    }
    .stTextArea textarea {
        height: 120px;
        font-size: 16px;
        border-radius: 8px;
    }
    .stButton button {
        background-color: #3498DB;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        padding: 10px 24px;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #2980B9;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .analysis-section {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #3498DB;
        margin-top: 20px;
    }
    /* Responsive design: adjust for screens narrower than 768px */
    @media screen and (max-width: 768px) {
        .stTextArea textarea, .stButton button, .stFileUploader, video {
            max-width: 100% !important;
        }
        /* Force columns to stack vertically on mobile */
        [data-testid="column"] {
            flex: 0 0 100% !important;
            max-width: 100% !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">BJJ Video Analyzer 🥋</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Powered by Gemini 2.0 Flash</p>', unsafe_allow_html=True)

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Jiu-jitsu.svg/320px-Jiu-jitsu.svg.png", width=150)
    st.header("About This Tool")
    st.markdown("""
    This analyzer provides technical BJJ feedback from uploaded videos using advanced AI.
    
    **Features:**
    - Skill level assessment
    - Technical feedback
    - Targeted improvement drills
    - Coaching insights
    
    **Models:**
    - Gemini 2.0 Flash for video analysis
    """)
    st.divider()
    st.markdown("**Created by:** Apply, Co.")

@st.cache_resource
def initialize_agent():
    """Initialize and cache the Phi Agent with Gemini model."""
    return Agent(
        name="BJJ Video Analyzer",
        model=Gemini(id="gemini-2.0-flash-exp"),
        tools=[DuckDuckGo()],
        markdown=True,
    )

multimodal_Agent = initialize_agent()

col1, col2 = st.columns([3, 2])
with col1:
    video_file = st.file_uploader(
        "Upload a BJJ technique video", 
        type=['mp4', 'mov', 'avi'], 
        help="Upload a video of BJJ techniques for expert AI analysis"
    )

if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name
    
    st.video(video_path, format="video/mp4", start_time=0)
    
    query_col1, query_col2 = st.columns([3, 1])
    with query_col1:
        user_query = st.text_area(
            "What would you like to know about this technique?",
            placeholder="Examples: 'Analyze this armbar setup', 'What am I doing wrong with this guard pass?', 'How can I improve my transitions?'",
            help="Be specific about what aspects you want feedback on."
        )
    with query_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_button = st.button("🔍 Analyze Technique", key="analyze_video_button", use_container_width=True)
    
    if analyze_button:
        if not user_query:
            st.warning("⚠️ Please enter a question or insight to analyze the video.")
        else:
            try:
                with st.spinner("🔄 Processing video and generating expert BJJ feedback..."):
                    progress_bar = st.progress(0)
                    progress_bar.progress(10, text="Uploading video...")
                    processed_video = upload_file(video_path)
                    
                    progress_bar.progress(30, text="Processing video...")
                    processing_start = time.time()
                    while processed_video.state.name == "PROCESSING":
                        if time.time() - processing_start > 60:
                            st.warning("Video processing is taking longer than expected. Please be patient.")
                        time.sleep(1)
                        processed_video = get_file(processed_video.name)
                    
                    progress_bar.progress(60, text="Generating analysis...")
                    
                    analysis_prompt = f"""You are Professor Garcia, an IBJJF Hall of Fame BJJ coach with extensive competition and teaching experience. Analyze this BJJ video and address: {user_query}

First, determine the practitioner's skill level (beginner, intermediate, advanced, elite) based on movement fluidity, technical precision, and conceptual understanding.

Structure your analysis as follows:

## SKILL ASSESSMENT
Categorize the practitioner's level with specific observations of their technical execution. Example: "Intermediate: Shows understanding of basic mechanics but struggles with weight distribution during transitions."

## KEY STRENGTHS (2-3)
• Identify technically sound elements with timestamps  
• Explain why these elements demonstrate good Jiu-Jitsu

## CRITICAL IMPROVEMENTS (2-3)
• Pinpoint the highest-leverage technical corrections needed with timestamps  
• Explain the biomechanical principles being violated  
• Note potential consequences in live rolling scenarios

## SPECIFIC DRILLS (1-2)
• Prescribe targeted exercises that address the identified weaknesses  
• Explain the correct feeling/sensation to aim for when practicing

## COACHING INSIGHT
One key conceptual understanding that would elevate their game

## STUDENT TAKEAWAY
A memorable principle they should internalize (think: "Position before submission")

Use precise BJJ terminology while remaining accessible. Balance encouragement with honest technical assessment. Keep your analysis under 400 words total.
"""
                    progress_bar.progress(80, text="Finalizing insights...")
                    response = multimodal_Agent.run(analysis_prompt, videos=[processed_video])
                    progress_bar.progress(100, text="Complete!")
                    time.sleep(0.5)
                    progress_bar.empty()
                
                st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                st.subheader("📋 Expert BJJ Analysis")
                st.markdown(response.content)
                st.markdown('</div>', unsafe_allow_html=True)
                
                feedback_col1, feedback_col2 = st.columns(2)
                with feedback_col1:
                    st.download_button(
                        label="💾 Save Analysis",
                        data=response.content,
                        file_name="bjj_technique_analysis.md",
                        mime="text/markdown"
                    )
                with feedback_col2:
                    st.button("👍 This analysis was helpful", key="feedback_helpful")
            except Exception as error:
                show_toast(f"An error occurred: {error}")
                st.error(f"An error occurred during analysis: {error}")
                st.info("Try uploading a shorter video or check your internet connection.")
            finally:
                Path(video_path).unlink(missing_ok=True)
else:
    st.info("📤 Upload a BJJ video to receive expert analysis and personalized feedback.")
    with st.expander("ℹ️ How to get the best analysis"):
        st.markdown("""
        1. **Video Quality**: Ensure good lighting and a clear view of the technique.
        2. **Video Length**: Keep videos under 2 minutes for optimal analysis.
        3. **Specific Questions**: Ask targeted questions about specific aspects of the technique.
        4. **Multiple Angles**: If possible, show the technique from different angles.
        """)
