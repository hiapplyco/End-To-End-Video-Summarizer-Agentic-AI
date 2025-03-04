import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
import google.generativeai as genai
from google.generativeai import upload_file, get_file
from elevenlabs.client import ElevenLabs

import time
import os
import tempfile
from pathlib import Path
import base64

# Set page configuration as the first Streamlit command
st.set_page_config(
    page_title="Studio 540 - Technical BJJ Feedback in seconds",
    page_icon="🥋",
    layout="wide"
)

# ------------------------------
# Utility Functions for Background
# ------------------------------
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = f'''
    <style>
    :root {{
        --gi-blue: #1a365d;
        --mat-red: #c53030;
        --belt-gold: #d69e2e;
        --off-white: #f7fafc;
        --dark-text: #2d3748;
        --light-text: #f7fafc;
        --shadow: rgba(0, 0, 0, 0.15);
    }}
    .stApp {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0.65)), url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        color: var(--dark-text) !important;
    }}
    header {{
        display: none !important;
    }}
    .main .block-container {{
        padding: 2rem 1rem;
        max-width: 1100px;
        margin: 0 auto;
    }}
    h1, h2, h3 {{
        background-color: var(--gi-blue);
        color: var(--light-text) !important;
        padding: 1rem 1.5rem !important;
        border-radius: 8px !important;
        margin-bottom: 1.5rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 6px var(--shadow);
    }}
    p {{
        background-color: var(--off-white);
        color: var(--dark-text) !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 2px 4px var(--shadow);
    }}
    .stButton button {{
        background-color: var(--mat-red) !important;
        color: var(--light-text) !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px var(--shadow) !important;
    }}
    .stButton button:hover {{
        background-color: #b52a2a !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px var(--shadow) !important;
    }}
    [data-testid="stFileUploader"] {{
        background-color: var(--off-white) !important;
        padding: 2rem !important;
        border-radius: 10px !important;
        margin-bottom: 2rem !important;
        border: 2px dashed var(--belt-gold) !important;
        box-shadow: 0 4px 6px var(--shadow) !important;
    }}
    .stTextInput input, .stTextArea textarea {{
        background-color: var(--off-white) !important;
        color: var(--dark-text) !important;
        border: 1px solid #e2e8f0 !important;
        padding: 0.75rem 1rem !important;
        border-radius: 8px !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: var(--gi-blue) !important;
        color: var(--light-text) !important;
    }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
        background: none !important;
        color: var(--light-text) !important;
        padding: 0.5rem 0 !important;
        box-shadow: none !important;
    }}
    [data-testid="stSidebar"] p {{
        background: none !important;
        color: var(--light-text) !important;
        padding: 0.25rem 0 !important;
        box-shadow: none !important;
    }}
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] .stTextInput input,
    [data-testid="stSidebar"] .stSelectbox div,
    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] [data-baseweb="select"] {{
        background-color: var(--off-white) !important;
        color: var(--dark-text) !important;
    }}
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] caption,
    [data-testid="stSidebar"] .stMarkdown div {{
        color: var(--light-text) !important;
    }}
    [data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="tag"],
    [data-testid="stSidebar"] [data-baseweb="select"] span {{
        color: var(--dark-text) !important;
    }}
    div[data-baseweb="popover"] div[data-baseweb="menu"] {{
        background-color: var(--off-white) !important;
    }}
    div[data-baseweb="popover"] div[data-baseweb="menu"] li {{
        color: var(--dark-text) !important;
    }}
    [data-testid="stSidebar"] .streamlit-expanderHeader {{
        color: var(--light-text) !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }}
    [data-testid="stSidebar"] .streamlit-expanderContent {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: var(--light-text) !important;
        border-radius: 0 0 8px 8px !important;
    }}
    .testimonial {{
        background-color: var(--off-white) !important;
        border-left: 5px solid var(--gi-blue) !important;
        padding: 1.5rem !important;
        border-radius: 8px !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 4px 12px var(--shadow) !important;
        color: var(--dark-text) !important;
    }}
    .analysis-section {{
        background-color: var(--off-white) !important;
        border-left: 5px solid var(--belt-gold) !important;
        border-radius: 10px !important;
        padding: 2rem !important;
        margin-top: 2rem !important;
        box-shadow: 0 6px 18px var(--shadow) !important;
        color: var(--dark-text) !important;
    }}
    .stExpander {{
        background-color: var(--off-white) !important;
        border-radius: 8px !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 2px 4px var(--shadow) !important;
    }}
    [data-testid="stVideo"] {{
        border-radius: 8px !important;
        overflow: hidden !important;
        margin: 1.5rem 0 !important;
        box-shadow: 0 4px 12px var(--shadow) !important;
        border: 3px solid var(--gi-blue) !important;
    }}
    .stProgress > div > div {{
        background-color: var(--mat-red) !important;
    }}
    .stAudio {{
        background-color: var(--off-white) !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        margin-top: 1.5rem !important;
        box-shadow: 0 2px 4px var(--shadow) !important;
    }}
    [data-testid="column"] {{
        padding: 0.5rem !important;
    }}
    hr {{
        margin: 2rem 0 !important;
        border-color: var(--belt-gold) !important;
    }}
    .main {{
        color: var(--dark-text) !important;
    }}
    .main div, .main span, .main p, .main label {{
        color: var(--dark-text) !important;
    }}
    img {{
        margin: 1rem 0 !important;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# ------------------------------
# Set background image if available
# ------------------------------
background_image = "image_fx_ (18).jpg"
if os.path.exists(background_image):
    set_background(background_image)

# ------------------------------
# Retrieve API keys from secrets
# ------------------------------
API_KEY_GOOGLE = st.secrets["google"]["api_key"]
API_KEY_ELEVENLABS = st.secrets.get("elevenlabs", {}).get("api_key", None)

# ------------------------------
# Configure Google Generative AI
# ------------------------------
if API_KEY_GOOGLE:
    os.environ["GOOGLE_API_KEY"] = API_KEY_GOOGLE
    genai.configure(api_key=API_KEY_GOOGLE)
else:
    st.error("Google API Key not found. Please set the GOOGLE_API_KEY in Streamlit secrets.")
    st.stop()

# ------------------------------
# Basic CSS styling and responsive layout
# ------------------------------
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
    @media screen and (max-width: 768px) {
        [data-testid="column"] {
            flex: 0 0 100% !important;
            max-width: 100% !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------
# Header
# ------------------------------
col1, col2 = st.columns([1, 3])
with col1:
    st.image("https://www.studio540.com/wp-content/uploads/2023/03/clear_logo.png", width=200)
with col2:
    st.title("BJJ Video Analyzer")
    st.write("Powered by Gemini 2.0 Flash")

# ------------------------------
# Sidebar content
# ------------------------------
with st.sidebar:
    st.image("https://www.studio540.com/wp-content/uploads/2023/03/clear_logo.png", width=150)
    st.header("About Studio 540")
    st.write("""
    We open our doors to practitioners from any school and of any art with no judgments or biases.
    Our goal is to offer an environment where we can simply share knowledge and positively influence students' lives.

    We offer adult and kids gi jiu jitsu, no-gi submission grappling, and Muay Thai classes in Solana Beach, San Diego, CA.
    """)

    st.subheader("Contact Us")
    st.write("""
    **Call**: (858) 792-7776

    **Address**: 540 Stevens Avenue Solana Beach, CA 92075

    **Email**: Frontdesk@studio540.com
    """)

# ------------------------------
# Agent initialization
# ------------------------------
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

# ------------------------------
# Session state initialization
# ------------------------------
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

if 'audio_generated' not in st.session_state:
    st.session_state.audio_generated = False

if 'show_audio_options' not in st.session_state:
    st.session_state.show_audio_options = False

# ------------------------------
# Main UI - Landing and Video Analysis
# ------------------------------
st.header("BLENDING THE JIU JITSU EXPERIENCE")
st.write("Upload a video of your BJJ technique to receive expert AI analysis and personalized feedback.")

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

                    st.session_state.analysis_result = response.content
                    st.session_state.audio_generated = False
                    st.session_state.show_audio_options = False

                st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                st.subheader("📋 Expert BJJ Analysis")
                st.markdown(st.session_state.analysis_result)
                st.markdown('</div>', unsafe_allow_html=True)

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
                    # Toggle the audio options panel
                    if st.button("🔊 Listen to Analysis"):
                        st.session_state.show_audio_options = True
                        st.experimental_rerun()

                # Add the audio options panel that appears when the button is clicked
                if st.session_state.show_audio_options:
                    with st.expander("🎧 Voice Selection", expanded=True):
                        st.subheader("Choose a voice for your analysis")

                        # Get the ElevenLabs API key from Streamlit secrets
                        elevenlabs_api_key = API_KEY_ELEVENLABS

                        # Voice selection
                        selected_voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID
                        if elevenlabs_api_key:
                            try:
                                client = ElevenLabs(api_key=elevenlabs_api_key)
                                voice_data = client.voices.get_all()
                                voices_list = [v.name for v in voice_data.voices]
                                selected_voice_name = st.selectbox("Choose Voice", options=voices_list, index=0)
                                selected_voice_id = next((v.voice_id for v in voice_data.voices if v.name == selected_voice_name), None)
                                if not selected_voice_id:
                                    st.warning("Could not match selected voice name. Using default voice ID.")
                                    selected_voice_id = "21m00Tcm4TlvDq8ikWAM"
                            except Exception:
                                st.warning("Could not retrieve voices. Using default voice ID.")
                                selected_voice_id = "21m00Tcm4TlvDq8ikWAM"
                        else:
                            st.error("ElevenLabs API key not found in Streamlit secrets.")

                        # Generate audio and close buttons
                        gen_col1, gen_col2 = st.columns([1, 1])
                        with gen_col1:
                            generate_button = st.button("Generate Audio", key="generate_audio_button")
                        with gen_col2:
                            close_button = st.button("Close", key="close_audio_panel")
                            if close_button:
                                st.session_state.show_audio_options = False
                                st.experimental_rerun()

                        # Generate audio when button is clicked
                        if generate_button:
                            if elevenlabs_api_key:
                                try:
                                    with st.spinner("Generating audio..."):
                                        clean_text = st.session_state.analysis_result.replace('#', '').replace('*', '')
                                        client = ElevenLabs(api_key=elevenlabs_api_key)
                                        audio = client.text_to_speech.convert(
                                            text=clean_text,
                                            voice_id=selected_voice_id,
                                            model_id="eleven_multilingual_v2"
                                        )
                                        st.session_state.audio = audio
                                        st.session_state.audio_generated = True

                                        # Show audio player and download button
                                        st.audio(audio, format="audio/mp3")
                                        st.download_button(
                                            label="💾 Save Audio",
                                            data=audio,
                                            file_name="bjj_analysis_audio.mp3",
                                            mime="audio/mp3"
                                        )
                                except Exception as e:
                                    st.error(f"Error generating audio: {str(e)}")
                            else:
                                st.error("ElevenLabs API key is required for text-to-speech.")

            except Exception as error:
                st.error(f"An error occurred during analysis: {error}")
                st.info("Try uploading a shorter video or check your internet connection.")
            finally:
                Path(video_path).unlink(missing_ok=True)
else:
    st.write("""
    We open our doors to practitioners from any school and of any art with no judgments or biases.
    Our goal is to offer an environment where we can simply share knowledge and positively influence students' lives.
    """)

    st.button("TRY A FREE CLASS")

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
        various clinching techniques. Emphasis is placed on accurate striking with fists, elbows, knees,
        and shins. Gloves and pads are used in class.
        """)

    st.divider()

    st.header("THE VALUE OF LEGACY: KNOWLEDGE AND PASSION PASSED ON")

    st.info("📤 Upload a BJJ video to receive expert analysis and personalized feedback.")

    with st.expander("ℹ️ How to get the best analysis"):
        st.markdown("""
        1. **Video Quality**: Ensure good lighting and a clear view of the technique.
        2. **Video Length**: Keep videos under 2 minutes for optimal analysis.
        3. **Specific Questions**: Ask targeted questions about specific aspects of the technique.
        4. **Multiple Angles**: If possible, show the technique from different angles.
        """)

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
