import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
import google.generativeai as genai
from google.generativeai import upload_file, get_file
from elevenlabs import generate, play, voices
from elevenlabs.api.error import UnauthenticatedRateLimitError, RateLimitError

import time
import os
import tempfile
from pathlib import Path
import base64

# Function to set background image from file
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = '''
    <style>
    .stApp {
        background-image: url("data:image/png;base64,%s");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }
    .stApp::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.85);
        z-index: -1;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Set background image if exists
if os.path.exists("assets/background.jpg"):
    set_background("assets/background.jpg")

# Retrieve API keys from secrets
API_KEY_GOOGLE = st.secrets["google"]["api_key"]
API_KEY_ELEVENLABS = st.secrets.get("elevenlabs", {}).get("api_key", None)

if API_KEY_GOOGLE:
    os.environ["GOOGLE_API_KEY"] = API_KEY_GOOGLE
    genai.configure(api_key=API_KEY_GOOGLE)
else:
    st.error("Google API Key not found. Please set the GOOGLE_API_KEY in Streamlit secrets.")
    st.stop()

# Basic page configuration
st.set_page_config(
    page_title="Studio 540 - BJJ Video Analyzer",
    page_icon="🥋",
    layout="wide"
)

# Basic CSS styling
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .header-container {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    .header-logo {
        width: 200px;
        margin-right: 2rem;
    }
    .analysis-section {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #3498DB;
        margin-top: 20px;
    }
    .testimonial {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
        font-style: italic;
    }
    </style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([1, 3])
with col1:
    st.image("https://www.studio540.com/wp-content/uploads/2023/03/clear_logo.png", width=200)
with col2:
    st.title("BJJ Video Analyzer")
    st.write("Powered by Gemini 2.0 Flash")

# Sidebar content
with st.sidebar:
    st.image("https://www.studio540.com/wp-content/uploads/2023/03/clear_logo.png", width=150)
    st.header("About Studio 540")
    st.write("""
    We open our doors to practitioners from any school and of any art with no judgments or biases. 
    Our goal is to offer an environment where we can simply share knowledge and positively influence students' lives.
    
    We offer adult and kids gi jiu jitsu, no-gi submission grappling, and Muay Thai classes in Solana Beach, San Diego, CA.
    """)
    
    # ElevenLabs API Key input in sidebar
    with st.expander("Voice Settings", expanded=False):
        st.caption("Configure text-to-speech settings")
        user_api_key = st.text_input("ElevenLabs API Key (optional)", 
                                     type="password",
                                     help="Enter your ElevenLabs API key for better quality and unlimited characters")
        # Use user-provided API key or fall back to the one in secrets
        elevenlabs_api_key = user_api_key if user_api_key else API_KEY_ELEVENLABS
        
        if elevenlabs_api_key:
            try:
                voice_options = [v.name for v in voices(api_key=elevenlabs_api_key)]
                selected_voice = st.selectbox("Choose Voice", options=voice_options, index=0)
            except Exception:
                st.warning("Could not retrieve voices. Using default voice.")
                selected_voice = "Adam"  # Default voice
        else:
            selected_voice = "Adam"  # Default voice
    
    st.subheader("Contact Us")
    st.write("""
    **Call**: (858) 792-7776
    
    **Address**: 540 Stevens Avenue Solana Beach, CA 92075
    
    **Email**: Frontdesk@studio540.com
    """)

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

# Initialize session state for storing the analysis result
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

if 'audio_generated' not in st.session_state:
    st.session_state.audio_generated = False

# Main UI
st.header("BLENDING THE JIU JITSU EXPERIENCE")
st.write("Upload a video of your BJJ technique to receive expert AI analysis and personalized feedback.")

# Video uploader
video_file = st.file_uploader(
    "Upload a BJJ technique video", 
    type=['mp4', 'mov', 'avi'], 
    help="Upload a video of BJJ techniques for expert AI analysis"
)

if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name
    
    # Display video
    st.video(video_path, format="video/mp4", start_time=0)

    # Query input and analyze button
    user_query = st.text_area(
        "What would you like to know about this technique?",
        placeholder="Examples: 'Analyze this armbar setup', 'What am I doing wrong with this guard pass?', 'How can I improve my transitions?'",
        height=120
    )
    
    analyze_button = st.button("🔍 Analyze Technique", key="analyze_video_button")

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
                
                    # Store the analysis result in session state
                    st.session_state.analysis_result = response.content
                    # Reset audio generated flag
                    st.session_state.audio_generated = False
                
                # Display analysis result
                st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                st.subheader("📋 Expert BJJ Analysis")
                st.markdown(st.session_state.analysis_result)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        label="💾 Save Analysis",
                        data=st.session_state.analysis_result,
                        file_name="bjj_technique_analysis.md",
                        mime="text/markdown"
                    )
                with col2:
                    st.button("👍 This analysis was helpful", key="feedback_helpful")
                with col3:
                    # Text-to-speech button
                    if st.button("🔊 Listen to Analysis"):
                        if elevenlabs_api_key:
                            try:
                                with st.spinner("Generating audio..."):
                                    # Extract text without markdown formatting for better speech
                                    clean_text = st.session_state.analysis_result.replace('#', '').replace('*', '')
                                    
                                    # Generate audio using ElevenLabs
                                    audio = generate(
                                        text=clean_text,
                                        voice=selected_voice,
                                        model="eleven_multilingual_v1",
                                        api_key=elevenlabs_api_key
                                    )
                                    
                                    # Store audio in session state
                                    st.session_state.audio = audio
                                    st.session_state.audio_generated = True
                                    
                                    # Force rerun to show audio player
                                    st.experimental_rerun()
                            except UnauthenticatedRateLimitError:
                                st.error("API rate limit exceeded. Please provide a valid ElevenLabs API key.")
                            except RateLimitError:
                                st.error("API rate limit reached. Try again later or use a different API key.")
                            except Exception as e:
                                st.error(f"Error generating audio: {str(e)}")
                        else:
                            st.error("ElevenLabs API key is required for text-to-speech. Please enter it in the sidebar.")
                
                # Display audio player if audio was generated
                if st.session_state.audio_generated and hasattr(st.session_state, 'audio'):
                    st.audio(st.session_state.audio, format="audio/mp3")
                    
            except Exception as error:
                st.error(f"An error occurred during analysis: {error}")
                st.info("Try uploading a shorter video or check your internet connection.")
            finally:
                # Clean up temporary file
                Path(video_path).unlink(missing_ok=True)
else:
    # Landing page content when no video is uploaded
    st.write("""
    We open our doors to practitioners from any school and of any art with no judgments or biases. 
    Our goal is to offer an environment where we can simply share knowledge and positively influence students' lives.
    """)
    
    st.button("TRY A FREE CLASS")
    
    # Martial arts offerings
    st.header("MARTIAL ARTS")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Jiu Jitsu")
        st.write("""
        Jiu Jitsu is a fighting system that has evolved from Japan, through Brazil and now to the US. 
        Incorporating the gi or kimono, BJJ involves taking down an opponent, controlling them, and 
        submitting them through the application of joint locks and chokes.
        """)
    
    with col2:
        st.subheader("No-Gi Submission Grappling")
        st.write("""
        Submission Grappling is practiced without the gi or kimono, and brings together techniques from 
        Folk and Freestyle Wrestling, Judo, Jiu-Jitsu, and Sambo. Similar to BJJ, the principles of 
        control and submission remain.
        """)
    
    with col3:
        st.subheader("Muay Thai")
        st.write("""
        Muay Thai or Thai boxing is a combat sport of Thailand that uses stand-up striking along with 
        various clinching techniques. Emphasis is placed on accurate striking with fists, elbows, knees 
        and shins. Gloves and pads are used in class.
        """)
    
    st.divider()
    
    # Legacy section
    st.header("THE VALUE OF LEGACY: KNOWLEDGE AND PASSION PASSED ON")
    
    st.info("📤 Upload a BJJ video to receive expert analysis and personalized feedback.")
    
    # Tips for best analysis
    with st.expander("ℹ️ How to get the best analysis"):
        st.markdown("""
        1. **Video Quality**: Ensure good lighting and a clear view of the technique.
        2. **Video Length**: Keep videos under 2 minutes for optimal analysis.
        3. **Specific Questions**: Ask targeted questions about specific aspects of the technique.
        4. **Multiple Angles**: If possible, show the technique from different angles.
        """)
    
    # Testimonials
    st.header("FROM OUR STUDENTS")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="testimonial">', unsafe_allow_html=True)
        st.markdown("""
        "Joining Studio 540 has been one of the best decisions I've made in the past couple of years. 
        The lessons learned in discipline and pushing myself to another level have been invaluable. 
        I feel lucky to have such great instructors!"
        
        **Jordan Jackson**, White Belt
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="testimonial">', unsafe_allow_html=True)
        st.markdown("""
        "This place is pure magic. Incredibly competent, warm people; impeccable facility; 
        awesome students and a great general vibe. The studio feels like a tight community of 
        kind, generous and awesome humans."
        
        **Paul Asoyan**, Blue Belt
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("**You fight the way you practice.**")
