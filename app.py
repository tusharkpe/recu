import streamlit as st
import os
import tempfile
import PyPDF2
import re
import json
from groq import Groq

# Set page configuration
st.set_page_config(page_title="Recruitment Agent", layout="wide")

# Initialize session state variables if they don't exist
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'job_description' not in st.session_state:
    st.session_state.job_description = ""
if 'ats_score' not in st.session_state:
    st.session_state.ats_score = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = ""
if 'improved_resume' not in st.session_state:
    st.session_state.improved_resume = ""

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Function to call Groq API
def call_groq_api(prompt, model="llama3-8b-8192"):
    # Use the API key from session state instead of hardcoded value
    client = Groq(api_key=st.session_state.groq_api_key)
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an AI recruitment assistant that helps with resume analysis, interview preparation, and resume improvement."},
                {"role": "user", "content": prompt}
            ],
            model=model,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"Error calling Groq API: {str(e)}")
        return None

# Function to analyze resume against job description
# Function to analyze resume against job description
def analyze_resume(resume_text, job_description):
    prompt = f"""
    Analyze the following resume against the job description. 
    Provide a detailed analysis of how well the resume matches the job requirements.
    Calculate an ATS score out of 100 based on keyword matching, relevant experience, and overall fit.
    
    Resume:
    {resume_text}
    
    Job Description:
    {job_description}
    
    Please provide the following in your response:
    1. ATS Score (out of 100)
    2. Key matching skills and experiences with ratings (1-5 scale, where 5 is excellent match and 1 is poor match)
    3. Missing skills or qualifications
    4. Overall assessment
    5. Recommendation (Selected if score >= 75, Not Selected if score < 75)
    
    Format your response as a JSON with the following structure:
    {{"ats_score": <score>, "matching_skills": [{{
        "skill": "<skill name>",
        "rating": <rating 1-5>,
        "comment": "<brief comment on strength/weakness>"}}], 
    "missing_skills": [<list of skills>], 
    "assessment": "<assessment text>", 
    "recommendation": "<Selected/Not Selected>"}}
    """
    
    result = call_groq_api(prompt)
    if result:
        try:
            # Extract JSON from the response
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result_json = json.loads(json_str)
                st.session_state.ats_score = result_json.get("ats_score")
                return result_json
            else:
                st.error("Could not parse the API response.")
                return None
        except Exception as e:
            st.error(f"Error parsing result: {str(e)}")
            return None
    return None

# Function to generate interview questions
def generate_interview_questions(resume_text, job_description, question_types, difficulty, num_questions):
    prompt = f"""
    Based on the following resume and job description, generate {num_questions} interview questions.
    The questions should be of the following types: {', '.join(question_types)}.
    The difficulty level should be: {difficulty}.
    
    Resume:
    {resume_text}
    
    Job Description:
    {job_description}
    
    Format your response as a list of questions with explanations for why each question is relevant.
    """
    
    return call_groq_api(prompt)

# Function to improve resume
def improve_resume(resume_text, job_description):
    prompt = f"""
    Improve the following resume to better match the job description. 
    Make it more ATS-friendly and highlight relevant skills and experiences.
    
    Resume:
    {resume_text}
    
    Job Description:
    {job_description}
    
    Please provide the improved resume in a professional format.
    """
    
    return call_groq_api(prompt)

# Function to answer questions about the resume
def resume_qa(resume_text, question):
    prompt = f"""
    Based on the following resume, please answer this question: {question}
    
    Resume:
    {resume_text}
    """
    
    return call_groq_api(prompt)

# Main UI
st.title("Recruitment Agent")
st.markdown("Smart Resume Analysis & Interview Preparation System")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    st.subheader("API Keys")
    groq_api_key = st.text_input("Groq API Key", type="password")
    if groq_api_key:
        st.session_state.groq_api_key = groq_api_key
    
    st.markdown("---")
    
    st.subheader("Theme")
    accent_color = st.color_picker("Accent Color", "#3498db")
    
    st.markdown("---")
    
    st.write("🚀 Recruitment Agent")
    st.write("v1.0.0")

# Check if API key is provided
if 'groq_api_key' not in st.session_state or not st.session_state.groq_api_key:
    st.warning("Please enter your API key in the sidebar to continue.")
    st.stop()

# Main tabs
tabs = st.tabs(["Resume Analysis", "Resume Q&A", "Interview Questions", "Resume Improvement", "Improved Resume"])

# Resume Analysis Tab
with tabs[0]:
    st.header("Resume Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
        if uploaded_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            st.session_state.resume_text = extract_text_from_pdf(tmp_file_path)
            os.unlink(tmp_file_path)  # Delete the temporary file
            
            st.success("Resume uploaded successfully!")
    
    with col2:
        st.session_state.job_description = st.text_area("Enter Job Description", height=300)
    
    if st.button("Analyze Resume") and st.session_state.resume_text and st.session_state.job_description:
        with st.spinner("Analyzing resume..."):
            analysis_result = analyze_resume(st.session_state.resume_text, st.session_state.job_description)
            if analysis_result:
                st.session_state.analysis_result = analysis_result
    
    if st.session_state.analysis_result:
        st.subheader("Analysis Results")
        
        # Display ATS score with a gauge
        score = st.session_state.ats_score
        st.markdown(f"### ATS Score: {score}/100")
        
        # Create a progress bar for the score
        st.progress(score/100)
        
        # Display recommendation with appropriate color
        recommendation = st.session_state.analysis_result.get("recommendation", "")
        if "Selected" in recommendation:
            st.success(f"Recommendation: {recommendation}")
        else:
            st.error(f"Recommendation: {recommendation}")
        
        # Display matching skills
        st.subheader("Matching Skills")
        matching_skills = st.session_state.analysis_result.get("matching_skills", [])
        for skill in matching_skills:
            if isinstance(skill, dict):
                # New format with ratings
                skill_name = skill.get("skill", "")
                rating = skill.get("rating", 0)
                comment = skill.get("comment", "")
                
                # Create a visual rating display
                stars = "⭐" * rating + "☆" * (5 - rating)
                
                # Determine if it's a strength or weakness
                if rating >= 4:
                    strength_label = "💪 Strength"
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{skill_name}** - {stars}")
                        st.write(f"*{comment}*")
                    with col2:
                        st.success(strength_label)
                elif rating <= 2:
                    weakness_label = "⚠️ Weakness"
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{skill_name}** - {stars}")
                        st.write(f"*{comment}*")
                    with col2:
                        st.warning(weakness_label)
                else:
                    # Neutral rating
                    st.write(f"**{skill_name}** - {stars}")
                    st.write(f"*{comment}*")
                
                st.markdown("---")
            else:
                # Handle old format (just strings)
                st.write(f"✅ {skill}")
        
        # Display missing skills
        st.subheader("Missing Skills")
        missing_skills = st.session_state.analysis_result.get("missing_skills", [])
        if missing_skills:
            for skill in missing_skills:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{skill}**")
                with col2:
                    st.error("❌ Missing")
                st.markdown("---")
        else:
            st.info("No missing skills identified!")
        
        # Display assessment
        st.subheader("Overall Assessment")
        st.write(st.session_state.analysis_result.get("assessment", ""))

# Resume Q&A Tab
with tabs[1]:
    st.header("Resume Q&A")
    
    if not st.session_state.resume_text:
        st.warning("Please upload a resume in the Resume Analysis tab first.")
    else:
        question = st.text_input("Ask a question about the resume")
        if st.button("Get Answer") and question:
            with st.spinner("Generating answer..."):
                answer = resume_qa(st.session_state.resume_text, question)
                if answer:
                    st.subheader("Answer")
                    st.write(answer)

# Interview Questions Tab
with tabs[2]:
    st.header("Interview Questions Generator")
    
    if not st.session_state.resume_text or not st.session_state.job_description:
        st.warning("Please upload a resume and enter a job description in the Resume Analysis tab first.")
    else:
        st.subheader("Select question types:")
        col1, col2, col3 = st.columns(3)
        with col1:
            basic = st.checkbox("Basic", value=True)
        with col2:
            technical = st.checkbox("Technical", value=True)
        with col3:
            coding = st.checkbox("Coding", value=True)
        
        question_types = []
        if basic:
            question_types.append("Basic")
        if technical:
            question_types.append("Technical")
        if coding:
            question_types.append("Coding")
        
        st.subheader("Question difficulty:")
        difficulty = st.select_slider("Select", options=["Easy", "Medium", "Hard"], value="Medium")
        
        st.subheader("Number of questions:")
        num_questions = st.slider("", min_value=1, max_value=10, value=3)
        
        if st.button("Generate Interview Questions") and question_types:
            with st.spinner("Generating interview questions..."):
                questions = generate_interview_questions(
                    st.session_state.resume_text, 
                    st.session_state.job_description,
                    question_types,
                    difficulty,
                    num_questions
                )
                if questions:
                    st.subheader("Generated Questions")
                    st.write(questions)

# Resume Improvement Tab
with tabs[3]:
    st.header("Resume Improvement")
    
    if not st.session_state.resume_text or not st.session_state.job_description:
        st.warning("Please upload a resume and enter a job description in the Resume Analysis tab first.")
    else:
        if st.button("Improve Resume"):
            with st.spinner("Improving resume..."):
                improved_resume = improve_resume(st.session_state.resume_text, st.session_state.job_description)
                if improved_resume:
                    st.session_state.improved_resume = improved_resume
                    st.success("Resume improved! Check the Improved Resume tab.")

# Improved Resume Tab
with tabs[4]:
    st.header("Improved Resume")
    
    if not st.session_state.improved_resume:
        st.warning("Please go to the Resume Improvement tab and click 'Improve Resume' first.")
    else:
        st.write(st.session_state.improved_resume)
        
        # Add a download button for the improved resume
        st.download_button(
            label="Download Improved Resume",
            data=st.session_state.improved_resume,
            file_name="improved_resume.txt",
            mime="text/plain"
        )
