import re

def parse_job_description(job_desc):
    skills = re.findall(r'skills: (.*)|proficient in (.*)', job_desc, re.IGNORECASE)
    skills = skills[0][0] or skills[0][1] if skills else ''
    experience = re.findall(r'(\d+\+ years)', job_desc, re.IGNORECASE) or ['0 years']
    education = re.findall(r'(BS|MS|PhD) in (.*)', job_desc, re.IGNORECASE) or ['No degree']
    soft_skills = re.findall(r'(teamwork|problem-solving|communication)', job_desc, re.IGNORECASE)
    must_haves = {
        'skills': [s.strip() for s in skills.split(',')] if skills else [],
        'experience_years': int(experience[0].split('+')[0]) if experience[0] != '0 years' else 0,
        'education': education[0][0] if education else 'None',
        'soft_skills': soft_skills
    }
    weights = {'skills': 50, 'experience': 30, 'education': 10, 'soft_skills': 10}
    return must_haves, weights

def parse_resume(resume_text):
    skills = re.findall(r'skills: (.*)', resume_text, re.IGNORECASE)
    skills = skills[0].split(', ') if skills else []
    experience = re.findall(r'(\d+) years', resume_text, re.IGNORECASE)
    experience = experience[0] if experience else '0'
    education = re.findall(r'(BS|MS|PhD) (.*)', resume_text, re.IGNORECASE)
    education = education[0][0] if education else 'None'
    soft_skills = re.findall(r'(teamwork|problem-solving|communication)', resume_text, re.IGNORECASE)
    return {
        'skills': [s.strip() for s in skills],
        'experience_years': int(experience),
        'education': education,
        'soft_skills': soft_skills
    }

def score_resume(resume_data, job_must_haves, weights):
    skill_match = sum(1 for s in resume_data['skills'] if any(s.lower() in js.lower() for js in job_must_haves['skills'])) / max(len(job_must_haves['skills']), 1) * weights['skills']
    exp_match = min(resume_data['experience_years'] / job_must_haves['experience_years'], 1) * weights['experience'] if job_must_haves['experience_years'] > 0 else 0
    edu_match = weights['education'] if resume_data['education'] == job_must_haves['education'] else (weights['education'] * 0.5 if resume_data['education'] in ['BS', 'MS', 'PhD'] else 0)
    soft_match = len(resume_data['soft_skills']) / max(len(job_must_haves['soft_skills']), 1) * weights['soft_skills']
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
            print(f"Error processing Resume {i}: {e}")
            scored_resumes.append((i, 0, "Invalid resume format"))
    scored_resumes.sort(key=lambda x: (-x[1], -int(re.search(r'(\d+) years', x[2]).group(1)) if re.search(r'(\d+) years', x[2]) else 0))
    print("Ranked Resumes (Best to Worst Match):")
    for rank, (num, score, reason) in enumerate(scored_resumes, 1):
        print(f"{rank}. Resume {num} - Score: {score}/100 - {reason}")

# Sample JD and resumes
job_desc = """Software Engineer Role
Requirements:
- 3+ years in software development
- Proficient in Python, Java
- BS in Computer Science
- Strong teamwork, problem-solving, communication"""

resumes = [
    """Resume 1
Skills: Python, Java
Experience: 5 years software dev
Education: BS CS
Soft Skills: teamwork, problem-solving""",
    """Resume 2
Skills: Python, Django
Experience: 4 years backend dev
Education: MS CS
Soft Skills: teamwork""",
    """Resume 3
Skills: Java, AWS
Experience: 2 years software dev
Education: BS CS
Soft Skills: problem-solving""",
    """Resume 4
Skills: Python, Java, AWS
Experience: 7 years software dev
Education: PhD CS
Soft Skills: teamwork, communication""",
    """Resume 5
Skills: C++, SQL
Experience: 5 years engineering
Education: BS EE
Soft Skills: problem-solving""",
    """Resume 6
Skills: Python
Experience: 6 years data analysis
Education: MBA
Soft Skills: communication""",
    """Resume 7
Skills: Java, Docker
Experience: 4 years software dev
Education: BS CS
Soft Skills: teamwork, communication""",
    """Resume 8
Skills: None
Experience: 10 years management
Education: BA
Soft Skills: teamwork, communication""",
    """Resume 9
Skills: Python, Java, Django
Experience: 3 years software dev
Education: BS CS
Soft Skills: problem-solving, communication""",
    """Resume 10
Skills: Java
Experience: 1 year software dev
Education: BS CS
Soft Skills: teamwork"""
]

run_agent(job_desc, resumes)
