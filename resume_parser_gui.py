import re
import streamlit as st
import tempfile
import fitz  # PyMuPDF
from docx import Document
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Predefined list of common technical skills (lowercased for matching)
common_technical_skills = [
    'python', 'java', 'c++', 'javascript', 'sql', 'c#', 'ruby', 'go', 'kotlin', 'swift', 'php',
    'react', 'angular', 'vue.js', 'node.js', 'django', 'flask', 'spring boot', 'asp.net',
    'aws', 'azure', 'google cloud', 'docker', 'kubernetes', 'jenkins', 'git', 'terraform',
    'mysql', 'postgresql', 'mongodb', 'redis', 'oracle',
    'html', 'css', 'typescript', 'rust', 'scala', 'perl',
    'ansible', 'puppet', 'chef', 'elasticsearch', 'kafka',
    'android', 'ios', 'flutter', 'react native'
]

# Degree levels for better matching (enhanced to include variations)
degree_levels = {
    'BS': 1, 'BSC': 1, 'BA': 1,
    'MS': 2, 'MSC': 2, 'MA': 2,
    'PHD': 3
}

def parse_job_description(job_desc):
    job_desc_lower = job_desc.lower()
    
    # Extract skills: find mentions of common technical skills
    skills = set()
    for skill in common_technical_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', job_desc_lower):
            skills.add(skill.capitalize())
    
    skills = list(skills)
    
    # Extract experience: find all \d+ years, take the maximum as min required
    experience_matches = re.findall(r'(\d+)\+? years?', job_desc_lower)
    experience_years = max([int(x) for x in experience_matches], default=0)
    
    # Extract education: find degrees, take the highest level
    edu_matches = re.findall(r'\b(bs|bsc|ba|ms|msc|ma|phd)\b', job_desc_lower)
    edu_levels = [degree_levels.get(edu.upper(), 0) for edu in edu_matches]
    education_level = max(edu_levels, default=0)
    
    # Soft skills: find mentions (fixed to match JD exactly)
    soft_possible = ['teamwork', 'communication']
    soft_skills = [s for s in soft_possible if re.search(r'\b' + re.escape(s) + r'\b', job_desc_lower)]
    
    must_haves = {
        'skills': skills,
        'experience_years': experience_years,
        'education_level': education_level,
        'soft_skills': soft_skills
    }
    weights = {'skills': 60, 'experience': 25, 'education': 10, 'soft_skills': 5}
    return must_haves, weights

def parse_resume(resume_text):
    resume_lower = resume_text.lower()
    
    # Extract skills: same as JD
    skills = set()
    for skill in common_technical_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', resume_lower):
            skills.add(skill.capitalize())
    
    skills = list(skills)
    
    # Extract experience: find all \d+ years, take the maximum
    experience_matches = re.findall(r'(\d+)\+? years?', resume_lower)
    experience_years = max([int(x) for x in experience_matches], default=0)
    
    # Extract education: find degrees, take the highest level
    edu_matches = re.findall(r'\b(bs|bsc|ba|ms|msc|ma|phd)\b', resume_lower)
    edu_levels = [degree_levels.get(edu.upper(), 0) for edu in edu_matches]
    education_level = max(edu_levels, default=0)
    
    # Soft skills: find mentions
    soft_possible = ['teamwork', 'communication']
    soft_skills = [s for s in soft_possible if re.search(r'\b' + re.escape(s) + r'\b', resume_lower)]
    
    return {
        'skills': skills,
        'experience_years': experience_years,
        'education_level': education_level,
        'soft_skills': soft_skills
    }

def score_resume(resume_data, job_must_haves, weights):
    if job_must_haves['skills']:
        skill_match = sum(1 for s in resume_data['skills'] if any(s.lower() in js.lower() for js in job_must_haves['skills'])) / len(job_must_haves['skills']) * weights['skills']
    else:
        skill_match = 0
    
    exp_match = min(resume_data['experience_years'] / job_must_haves['experience_years'], 1) * weights['experience'] if job_must_haves['experience_years'] > 0 else weights['experience'] if resume_data['experience_years'] > 0 else 0
    
    if resume_data['education_level'] >= job_must_haves['education_level']:
        edu_match = weights['education']
    elif resume_data['education_level'] > 0:
        edu_match = weights['education'] * 0.5
    else:
        edu_match = 0
    
    soft_match = len(set(resume_data['soft_skills'])) / max(len(job_must_haves['soft_skills']), 1) * weights['soft_skills']
    
    total = int(skill_match + exp_match + edu_match + soft_match)
    
    skills_str = ' and '.join(resume_data['skills']) if resume_data['skills'] else 'no technical'
    return total, f"{skills_str} skills and {resume_data['experience_years']} years experience"

def run_agent(job_desc, resumes):
    job_must_haves, weights = parse_job_description(job_desc)
    scored_resumes = []
    for i, resume in enumerate(resumes, 1):
        try:
            resume_data = parse_resume(resume)
            score, reason = score_resume(resume_data, job_must_haves, weights)
            scored_resumes.append((i, score, reason))
        except Exception as e:
            st.warning(f"Error processing Resume {i}: {e}")
            scored_resumes.append((i, 0, "Invalid resume format"))
    scored_resumes.sort(key=lambda x: (-x[1], -int(re.search(r'(\d+) years', x[2]).group(1)) if re.search(r'(\d+) years', x[2]) else 0))
    return scored_resumes

def extract_text_from_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {e}")

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from docx: {e}")

def extract_text_from_csv(file_path, column_name='description'):
    try:
        df = pd.read_csv(file_path)
        if column_name in df.columns:
            return "\n".join(df[column_name].astype(str).dropna())
        return ""
    except Exception as e:
        raise ValueError(f"Failed to extract text from CSV: {e}")

def extract_text_from_file(file_path):
    try:
        ext = os.path.splitext(file_path)[1].lower()
        st.write(f"Processing file: {file_path} with extension: {ext}")  # Debug logging
        if ext == '.pdf':
            return extract_text_from_pdf(file_path)
        elif ext in ['.docx', '.DOCX']:  # Explicitly handle both cases
            return extract_text_from_docx(file_path)
        elif ext == '.csv':
            return extract_text_from_csv(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    except Exception as e:
        raise ValueError(f"Error processing file {file_path}: {e}")

# Streamlit app
st.title("Resume Parser GUI")

# JD Input Section
st.header("Enter Job Description")
jd_option = st.radio("JD Input Type", ("Text", "File (CSV/PDF)"))

if jd_option == "Text":
    job_desc = st.text_area("Paste JD Text Here", height=200)
else:
    jd_file = st.file_uploader("Upload JD File (CSV or PDF)", type=['csv', 'pdf'])
    if jd_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=jd_file.name.lower()) as tmp:
            tmp.write(jd_file.read())
            tmp_path = tmp.name
        try:
            job_desc = extract_text_from_file(tmp_path)
            st.success(f"JD loaded successfully from {jd_file.name}!")
            st.text_area("Extracted JD Text", job_desc, height=200, disabled=True)
        except Exception as e:
            st.error(f"Error loading JD file {jd_file.name}: {e}")
            job_desc = ""
        finally:
            try:
                os.unlink(tmp_path)
            except Exception as e:
                st.warning(f"Failed to clean up temp file for JD: {e}")
    else:
        job_desc = ""

# Resumes Input Section
st.header("Enter Resumes")
resume_option = st.radio("Resume Input Type", ("Text", "File (PDF/Word)"))

resumes = []
resume_names = []
if resume_option == "Text":
    resume_text = st.text_area("Paste Resumes Here (separate each with '---')", height=300)
    if resume_text:
        resume_list = [r.strip() for r in resume_text.split('---') if r.strip()]
        resumes = resume_list
        resume_names = [f"Resume {i+1}" for i in range(len(resumes))]
else:
    resume_files = st.file_uploader("Upload Multiple Resumes (PDF or Word)", type=['pdf', 'docx', 'DOCX'], accept_multiple_files=True)
    if resume_files:
        for file in resume_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=file.name.lower()) as tmp:
                tmp.write(file.read())
                tmp_path = tmp.name
            try:
                st.write(f"Attempting to process resume: {file.name} at {tmp_path}")  # Debug
                resume_text = extract_text_from_file(tmp_path)
                resumes.append(resume_text)
                resume_names.append(file.name)
            except Exception as e:
                st.warning(f"Error loading resume {file.name}: {e}")
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception as e:
                    st.warning(f"Failed to clean up temp file for {file.name}: {e}")

# Run Button
if st.button("Run Parser", disabled=not (job_desc and resumes)):
    with st.spinner("Processing resumes..."):
        scored_resumes = run_agent(job_desc, resumes)
    
    # Display Output
    st.header("Ranked Resumes")
    if scored_resumes:
        data = []
        for rank, (num, score, reason) in enumerate(scored_resumes, 1):
            filename = resume_names[num - 1] if num <= len(resume_names) else f"Resume {num}"
            data.append({"Rank": rank, "Resume": filename, "Score": f"{score}/100", "Reason": reason})
        
        st.subheader("Results Table")
        st.dataframe(data, use_container_width=True)
        
        st.subheader("Score Visualization")
        scores = [score for _, score, _ in scored_resumes]
        labels = [resume_names[num - 1] if num <= len(resume_names) else f"Resume {num}" for num, _, _ in scored_resumes]
        
        fig, ax = plt.subplots()
        sns.barplot(x=scores, y=labels, ax=ax, palette='Blues_d')
        ax.set_xlabel("Score (out of 100)")
        ax.set_ylabel("Resumes")
        ax.set_title("Resume Scores")
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("No valid resumes processed.")
else:
    st.info("Enter a Job Description and provide at least one resume to run the parser.")

if __name__ == "__main__":
    pass  # Streamlit runs the script