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

# Set page configuration
st.set_page_config(
    page_title="Studio 540 - Technical BJJ Feedback",
    page_icon="🥋",
    layout="wide"
)

# ------------------------------
# Utility Functions for Background (REMOVED)
# ------------------------------
# Background and custom CSS are being significantly simplified for clarity.

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
# Basic CSS styling - now much simpler
# ------------------------------
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .analysis-section {
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #3498DB; /* Keeping a subtle accent */
        margin-top: 20px;
        background-color: #f9f9f9; /* Light background for analysis */
    }
    .stButton button {
        background-color: #3498DB;
        color: white;
    }
    .stDownloadButton button {
        background-color: #4CAF50; /* Example: Green for download */
        color: white;
    }

    /* Centralize elements for cleaner look on larger screens */
    .stFileUploader, .stTextArea, .stButton, .stDownloadButton, .stAudio, .stVideo {
        max-width: 800px; /* Adjust as needed */
        margin-left: auto;
        margin-right: auto;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------
# Header - Simplified
# ------------------------------
st.image("https://www.studio540.com/wp-content/uploads/2023/03/clear_logo.png", width=150) # Logo more prominent at top
st.title("BJJ Video Analyzer")
st.markdown("Get expert AI feedback on your Jiu-Jitsu techniques.") # Clear subtitle as CTA

# ------------------------------
# Sidebar content - Kept, but less visually emphasized by default styling
# ------------------------------
with st.sidebar:
    st.image("https://www.studio540.com/wp-content/uploads/2023/03/clear_logo.png", width=100) # Smaller sidebar logo
    st.header("About Studio 540", anchor=False) # anchor=False to remove streamlit warning
    st.write("""
    We welcome practitioners from all schools and arts, offering a knowledge-sharing environment to positively impact students' lives.

    Adult and kids classes in gi jiu jitsu, no-gi submission grappling, and Muay Thai in Solana Beach, San Diego, CA.
    """)

    st.subheader("Contact Us", anchor=False)
    st.write("""
    **Call**: (858) 792-7776

    **Address**: 540 Stevens Avenue, Solana Beach, CA 92075

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

script_agent = initialize_agent() # Initialize a second agent for script generation

# ------------------------------
# Session state initialization
# ------------------------------
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

if 'audio_script' not in st.session_state: # New session state for audio script
    st.session_state.audio_script = None

if 'audio_generated' not in st.session_state:
    st.session_state.audio_generated = False

if 'show_audio_options' not in st.session_state:
    st.session_state.show_audio_options = False

# ------------------------------
# Main UI - Streamlined Landing and Video Analysis
# ------------------------------
st.write(" ") # Adding some whitespace
st.write("To get started, upload a video of your BJJ technique below.") # More direct instruction

video_file = st.file_uploader(
    "Upload BJJ Video for Analysis", # Clearer label
    type=['mp4', 'mov', 'avi'],
    help="Upload a video of BJJ techniques to receive AI feedback."
)

if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name

    st.video(video_path, format="video/mp4", start_time=0)

    user_query = st.text_area(
        "What do you want to learn from this analysis?", # More user-focused question
        placeholder="e.g., 'Analyze this armbar setup', 'How to improve my guard pass?'",
        height=80 # Reduced height for text area
    )
    analyze_button = st.button("Analyze My Technique") # Stronger CTA button text

    if analyze_button:
        if not user_query:
            st.warning("Please enter a question to analyze the video.")
        else:
            try:
                with st.spinner("Analyzing video and generating expert BJJ feedback..."):
                    progress_bar = st.progress(0)
                    progress_bar.progress(10, text="Uploading...")
                    processed_video = upload_file(video_path)

                    progress_bar.progress(30, text="Processing...")
                    processing_start = time.time()
                    while processed_video.state.name == "PROCESSING":
                        if time.time() - processing_start > 60:
                            st.warning("Video processing is taking longer than expected. Please be patient.")
                        time.sleep(1)
                        processed_video = get_file(processed_video.name)

                    progress_bar.progress(60, text="Analyzing...")

                    analysis_prompt = f"""You are a legendary, Hall of Fame level Jiu-Jitsu coach, embodying the combined knowledge of the greatest BJJ practitioners in history.  You are known for your technical mastery, strategic brilliance, and ability to elevate any student's game. Analyze this BJJ video and address: {user_query}

Your analysis should be structured with the precision and depth of a world champion's mind, yet delivered with the clarity to resonate with any dedicated student.

Begin by immediately identifying the practitioner's skill level – from white belt fundamentals to black belt intricacies. Be direct and insightful in your assessment.

Structure your feedback rigorously, as follows:

## SKILL LEVEL DIAGNOSIS
Categorize the practitioner definitively (Beginner, Intermediate, Advanced, Elite).  Pinpoint specific indicators in their technique that justify this classification. Be as precise as you would when cornering a student for a world championship match. *Example: "Advanced: Demonstrates sophisticated guard retention and transitions, but subtle weight distribution errors in passing sequences are evident."*

## CORE STRENGTHS (Highlight 2-3 Key Areas)
*   Identify elements executed with technical brilliance. Include precise timestamps to guide focused review.
*   Articulate *why* these strengths are effective Jiu-Jitsu. Connect them to fundamental principles like leverage, balance disruption, or control.

## CRITICAL ADJUSTMENTS (Prioritize 2-3 High-Impact Corrections)
*   Zero in on the most crucial technical flaws hindering their progress. Provide timestamps for immediate visual reference.
*   Explain the violated biomechanical principles in clear, actionable terms.  Emphasize the *why* behind the correction, not just the *what*.
*   Detail the tangible consequences of these errors in live sparring or competition – what submissions are they vulnerable to, what positions will they lose?

## TARGETED DRILLS (Prescribe 1-2 Game-Changing Exercises)
*   Recommend specific, focused drills to directly address the identified weaknesses. These should be drills used by champions to hone their skills.
*   Describe the *precise feeling* and *sensory cues* the practitioner should seek during drilling to ensure correct execution and accelerate learning.

## COACHING WISDOM (The 'X-Factor' Insight)
Articulate one profound, high-level Jiu-Jitsu concept or strategic understanding that, if internalized, would represent a significant leap in their overall game. This should be the kind of wisdom passed down from generation to generation of BJJ masters.

## STUDENT'S MANDATE (The Key Takeaway)
Conclude with a single, memorable principle – a 'mantra' – that the student must engrave into their Jiu-Jitsu philosophy.  Think: "Control the Center," "Always Improve Your Base," or "Patience is Submission."

Deliver your analysis with the authority of a legend, yet with the clarity and encouragement needed to inspire growth. Use precise BJJ terminology, but ensure accessibility. Be direct, honest, and above all, actionable.  Keep your analysis concise and impactful – under 2500 words, as befits the efficient communication of a true master.
"""
                    progress_bar.progress(80, text="Generating Insights...")
                    response = multimodal_Agent.run(analysis_prompt, videos=[processed_video])
                    progress_bar.progress(100, text="Complete!")
                    time.sleep(0.5)
                    progress_bar.empty()

                    st.session_state.analysis_result = response.content
                    st.session_state.audio_generated = False
                    st.session_state.show_audio_options = False
                    st.session_state.audio_script = None # Reset audio script when new analysis is generated

            except Exception as error:
                st.error(f"Analysis error: {error}")
                st.info("Try a shorter video or check your connection.")
            finally:
                Path(video_path).unlink(missing_ok=True)

    # Analysis Section - Displayed regardless of audio options
    if st.session_state.analysis_result:
        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
        st.subheader("Expert BJJ Analysis")
        st.markdown(st.session_state.analysis_result)
        st.markdown('</div>', unsafe_allow_html=True)

        st.download_button(
            label="Download Analysis", # Clearer label
            data=st.session_state.analysis_result,
            file_name="bjj_technique_analysis.md",
            mime="text/markdown"
        )

        # Audio Options Section - Now consistently below analysis
        if st.button("Listen to Analysis (Audio Options)"): # More informative button
            st.session_state.show_audio_options = True

        if st.session_state.show_audio_options:
            with st.expander("Audio Voice Settings", expanded=True): # Clearer expander title
                st.subheader("Voice Options")

                elevenlabs_api_key = API_KEY_ELEVENLABS
                selected_voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID
                if elevenlabs_api_key:
                    try:
                        client = ElevenLabs(api_key=elevenlabs_api_key)
                        voice_data = client.voices.get_all()
                        voices_list = [v.name for v in voice_data.voices]
                        selected_voice_name = st.selectbox("Choose Voice", options=voices_list, index=0)
                        selected_voice_id = next((v.voice_id for v in voice_data.voices if v.name == selected_voice_name), None)
                        if not selected_voice_id:
                            st.warning("Voice selection issue. Using default voice.")
                            selected_voice_id = "21m00Tcm4TlvDq8ikWAM"
                    except Exception as e:
                        st.warning(f"Could not retrieve voices: {e}. Using default voice.") # Include error in warning
                        selected_voice_id = "21m00Tcm4TlvDq8ikWAM"
                else:
                    st.error("ElevenLabs API key missing.")

                if st.button("Generate Audio Analysis"): # Clear CTA for audio generation
                    if elevenlabs_api_key:
                        try:
                            with st.spinner("Preparing audio script..."): # New spinner for script generation
                                script_prompt = f"""
                                Convert the following Jiu-Jitsu technique analysis into a natural, enthusiastic, and encouraging monologue script as if spoken by a seasoned BJJ coach.

                                Remove all headings, bullet points, timestamps or any special characters.  The script should be plain text and flow naturally when read aloud.  Imagine you are Professor Garcia, speaking directly to your student, providing feedback and motivation.

                                Maintain all the technical insights and recommendations from the analysis, but phrase them in a conversational, easy-to-listen manner. Inject enthusiasm and a positive coaching tone.

                                **Analysis to convert:**
                                ```
                                {st.session_state.analysis_result}
                                ```
                                """
                                script_response = script_agent.run(script_prompt) # Use script_agent
                                st.session_state.audio_script = script_response.content # Store the script

                            with st.spinner("Generating audio..."):
                                clean_text = st.session_state.audio_script # Use audio_script for TTS
                                client = ElevenLabs(api_key=elevenlabs_api_key)
                                # **Modified Audio Generation Code:**
                                audio_generator = client.text_to_speech.convert(
                                    text=clean_text,
                                    voice_id=selected_voice_id,
                                    model_id="eleven_multilingual_v2"
                                )
                                audio_bytes = b"" # Initialize empty bytes
                                for chunk in audio_generator:
                                    audio_bytes += chunk # Accumulate audio chunks
                                st.session_state.audio = audio_bytes # Store audio bytes in session state
                                st.session_state.audio_generated = True

                                st.audio(st.session_state.audio, format="audio/mp3") # Play audio from bytes
                                st.download_button(
                                    label="Download Audio Analysis", # Clearer label
                                    data=st.session_state.audio, # Download audio from bytes
                                    file_name="bjj_analysis_audio.mp3",
                                    mime="audio/mp3"
                                )
                        except Exception as e:
                            st.error(f"Audio generation error: {str(e)}") # Include error in error message
                    else:
                        st.error("ElevenLabs API key needed for audio.")

else:
    st.write("""
    Welcome! Studio 540 provides expert analysis of your BJJ techniques in seconds.
    Upload a video to get started.
    """)
    st.info("🥋 Upload a BJJ video above to receive expert AI analysis and personalized feedback.") # Info message as CTA
    st.subheader("Get the Best Analysis") # Tips section
    with st.expander("Tips for Video Analysis"):
        st.markdown("""
        1. **Video Quality**: Good lighting, clear technique view.
        2. **Video Length**: Under 2 minutes for best results.
        3. **Specific Questions**: Ask targeted questions.
        4. **Multiple Angles**: Show technique from different views if possible.
        """)

    st.subheader("Explore Our Martial Arts Programs") # Section header
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### Jiu Jitsu") # Sub-subheader for better visual hierarchy
        st.write("""
        Gi Jiu Jitsu: Take down, control, and submit with joint locks and chokes.
        """)
    with col2:
        st.markdown("### No-Gi Grappling")
        st.write("""
        No-Gi: Submission grappling inspired by Wrestling, Judo, and Sambo.
        """)
    with col3:
        st.markdown("### Muay Thai")
        st.write("""
        Muay Thai: Stand-up striking and clinching from Thailand.
        """)

    st.markdown("---") # Divider for visual separation

    st.subheader("Student Success Stories") # Testimonials section
    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        "Studio 540 has been invaluable. Discipline and pushing my limits here are unmatched. Great instructors!" - Jordan Jackson
        """)
    with col2:
        st.info("""
        "Pure magic. Competent, warm people, great facility, awesome community. Studio 540 is special." - Paul Asoyan
        """)

    st.write("**Practice makes perfect.**") # Motivational quote
