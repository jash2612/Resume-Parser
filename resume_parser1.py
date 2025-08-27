import re

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
            skills.add(skill.capitalize())  # Capitalize for display
    
    skills = list(skills)
    
    # Extract experience: find all \d+ years, take the maximum as min required
    experience_matches = re.findall(r'(\d+)\+? years?', job_desc_lower)
    experience_years = max([int(x) for x in experience_matches], default=0)
    
    # Extract education: find degrees, take the highest level
    edu_matches = re.findall(r'\b(bs|bsc|ba|ms|msc|ma|phd)\b', job_desc_lower)
    edu_levels = [degree_levels.get(edu.upper(), 0) for edu in edu_matches]
    education_level = max(edu_levels, default=0)
    
    # Soft skills: find mentions
    soft_possible = ['teamwork', 'problem-solving', 'communication']
    soft_skills = [s for s in soft_possible if re.search(r'\b' + re.escape(s) + r'\b', job_desc_lower)]
    
    must_haves = {
        'skills': skills,
        'experience_years': experience_years,
        'education_level': education_level,
        'soft_skills': soft_skills
    }
    weights = {'skills': 50, 'experience': 30, 'education': 10, 'soft_skills': 10}
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
    soft_possible = ['teamwork', 'problem-solving', 'communication']
    soft_skills = [s for s in soft_possible if re.search(r'\b' + re.escape(s) + r'\b', resume_lower)]
    
    return {
        'skills': skills,
        'experience_years': experience_years,
        'education_level': education_level,
        'soft_skills': soft_skills
    }

def score_resume(resume_data, job_must_haves, weights):
    # Skill match: fraction of job skills matched by resume (using contains for partial match)
    if job_must_haves['skills']:
        skill_match = sum(1 for s in resume_data['skills'] if any(s.lower() in js.lower() for js in job_must_haves['skills'])) / len(job_must_haves['skills']) * weights['skills']
    else:
        skill_match = 0
    
    # Experience match
    exp_match = min(resume_data['experience_years'] / job_must_haves['experience_years'], 1) * weights['experience'] if job_must_haves['experience_years'] > 0 else weights['experience'] if resume_data['experience_years'] > 0 else 0
    
    # Education match: full if >= required, half if has any degree, else 0
    if resume_data['education_level'] >= job_must_haves['education_level']:
        edu_match = weights['education']
    elif resume_data['education_level'] > 0:
        edu_match = weights['education'] * 0.5
    else:
        edu_match = 0
    
    # Soft skills match
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
            print(f"Error processing Resume {i}: {e}")
            scored_resumes.append((i, 0, "Invalid resume format"))
    # Sort by score descending, then by experience descending
    scored_resumes.sort(key=lambda x: (-x[1], -int(re.search(r'(\d+) years', x[2]).group(1)) if re.search(r'(\d+) years', x[2]) else 0))
    print("Ranked Resumes (Best to Worst Match):")
    for rank, (num, score, reason) in enumerate(scored_resumes, 1):
        print(f"{rank}. Resume {num} - Score: {score}/100 - {reason}")

def main():
    print("Enter the Job Description (multi-line input, end with blank line):")
    job_lines = []
    while True:
        line = input()
        if not line:
            break
        job_lines.append(line)
    job_desc = '\n'.join(job_lines)
    
    num_resumes = int(input("Enter the number of resumes: "))
    resumes = []
    for i in range(num_resumes):
        print(f"Enter Resume {i+1} (multi-line input, end with blank line):")
        resume_lines = []
        while True:
            line = input()
            if not line:
                break
            resume_lines.append(line)
        resumes.append('\n'.join(resume_lines))
    
    run_agent(job_desc, resumes)

if __name__ == "__main__":
    main()