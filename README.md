# AI Video Summarizer

This is a **Video Summarizer** application that uses **Agentic AI with Phidata** and **Google Gemini AI** to analyze video content and generate meaningful summaries. The app also supports querying the video content using an AI-powered agent integrated with tools for web searches to enhance its responses.

## Features

- **Video Summarization**: Upload a video file and get a detailed summary of its content.
- **Query-Based Insights**: Ask questions about the video and receive intelligent answers.
- **Web Search Integration**: Perform supplementary web searches for additional context related to the video content.
- **Cloud Integration**: Option to handle large video files by streaming them to cloud storage like AWS S3.

## Technology Stack

- **Frontend**: Streamlit for an interactive user interface.
- **AI Model**: Google Gemini AI (Gen 2.0 Flash experimental model).
- **Other Tools**:
  - DuckDuckGo Search for web queries.
  - Cloud platforms (AWS, GCP) for large file handling.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/video-summarizer.git
   cd video-summarizer
   
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt

3. Set up environment variables:

- Create a .env file.
- Add your Google Gemini AI API key:
   ```bash
   GOOGLE_API_KEY=your_api_key

# Usage

## Run the Application
To start the application, use the following command:
```bash
streamlit run app.py
```
- Open the application in your browser.
- Upload a video file (max 200 MB). For larger files, follow the cloud integration steps.
- Use the query box to ask questions about the video or summarize its content.
- Analyze results directly in the app.



## Feedback

If you have any feedback, please reach out to us at midhunbose2017@gmail.com

