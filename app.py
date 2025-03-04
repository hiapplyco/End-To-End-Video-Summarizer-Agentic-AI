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
from dotenv import load_dotenv

API_KEY = os.getenv("GOOGLE_API_KEY")  # Try environment variable first
if not API_KEY and 'google' in st.secrets:  # Then check Streamlit secrets
    API_KEY = st.secrets["google"]["api_key"]

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.error("Google API Key not found. Please set the GOOGLE_API_KEY environment variable or configure it in Streamlit secrets.")
    st.stop()
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.error("Google API Key not found. Please set the GOOGLE_API_KEY environment variable.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Multimodal AI Agent - BJJ Video Analyzer",
    page_icon="🥋",
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        color: #2C3E50;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #7F8C8D;
        margin-bottom: 30px;
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
    </style>
""", unsafe_allow_html=True)

# Application Header
st.markdown('<h1 class="main-header">BJJ Video Analyzer 🥋</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Powered by Gemini 2.0 Flash</p>', unsafe_allow_html=True)

# Sidebar for application info
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
        model=Gemini(id="gemini-2.0-flash"),
        tools=[DuckDuckGo()],
        markdown=True,
    )

# Initialize the agent
multimodal_Agent = initialize_agent()

# File uploader in main section
col1, col2 = st.columns([3, 2])

with col1:
    video_file = st.file_uploader(
        "Upload a BJJ technique video", 
        type=['mp4', 'mov', 'avi'], 
        help="Upload a video of BJJ techniques for expert AI analysis"
    )

# Processing logic
if video_file:
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name
    
    # Display video
    st.video(video_path, format="video/mp4", start_time=0)
    
    # Create columns for a more compact interface
    query_col1, query_col2 = st.columns([3, 1])
    
    with query_col1:
        user_query = st.text_area(
            "What would you like to know about this technique?",
            placeholder="Examples: 'Analyze this armbar setup', 'What am I doing wrong with this guard pass?', 'How can I improve my transitions?'",
            help="Be specific about what aspects you want feedback on."
        )
    
    with query_col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        analyze_button = st.button("🔍 Analyze Technique", key="analyze_video_button", use_container_width=True)
    
    if analyze_button:
        if not user_query:
            st.warning("⚠️ Please enter a question or insight to analyze the video.")
        else:
            try:
                with st.spinner("🔄 Processing video and generating expert BJJ feedback..."):
                    # Progress bar for better UX
                    progress_bar = st.progress(0)
                    
                    # Upload and process video file
                    progress_bar.progress(10, text="Uploading video...")
                    processed_video = upload_file(video_path)
                    
                    # Wait for processing to complete
                    progress_bar.progress(30, text="Processing video...")
                    processing_start = time.time()
                    while processed_video.state.name == "PROCESSING":
                        # Check if processing is taking too long
                        if time.time() - processing_start > 60:
                            st.warning("Video processing is taking longer than expected. Please be patient.")
                        time.sleep(1)
                        processed_video = get_file(processed_video.name)
                    
                    progress_bar.progress(60, text="Generating analysis...")
                    
                    # Enhanced prompt for better BJJ-specific analysis
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

                    # AI agent processing
                    progress_bar.progress(80, text="Finalizing insights...")
                    response = multimodal_Agent.run(analysis_prompt, videos=[processed_video])
                    progress_bar.progress(100, text="Complete!")
                    time.sleep(0.5)
                    progress_bar.empty()

                # Display the result
                st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                st.subheader("📋 Expert BJJ Analysis")
                st.markdown(response.content)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Add feedback and save options
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
                st.error(f"An error occurred during analysis: {error}")
                st.info("Try uploading a shorter video or check your internet connection.")
            finally:
                # Clean up temporary video file
                Path(video_path).unlink(missing_ok=True)
else:
    # Display placeholder when no video is uploaded
    st.info("📤 Upload a BJJ video to receive expert analysis and personalized feedback.")
    
    # Example section
    with st.expander("ℹ️ How to get the best analysis"):
        st.markdown("""
        1. **Video Quality**: Ensure good lighting and a clear view of the technique
        2. **Video Length**: Keep videos under 2 minutes for optimal analysis
        3. **Specific Questions**: Ask targeted questions about specific aspects of the technique
        4. **Multiple Angles**: If possible, show the technique from different angles
        """)
