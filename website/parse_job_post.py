import re
import nltk
from collections import namedtuple

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

JobPost = namedtuple('JobPost', ['job_title', 'company_name', 'job_location', 'job_type', 'job_description',
                                 'job_requirements', 'preferred_qualifications', 'skills', 'responsibilities',
                                 'salary_range', 'benefits', 'application_deadline', 'application_instructions',
                                 'contact_information', 'company_culture', 'equal_opportunity_statement',
                                 'career_growth_opportunities', 'work_schedule', 'remote_work_options'])

def extract_job_title(text):
    # Customize this list according to the job titles you want to extract
    job_titles = {'Software Engineer', 'Data Scientist', 'Project Manager', 'Web Developer'}

    for job_title in job_titles:
        if re.search(r'\b' + job_title + r'\b', text, re.IGNORECASE):
            return job_title
    return None

def extract_email(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email = re.search(email_pattern, text)
    return email.group(0) if email else None

def extract_phone(text):
    phone_pattern = r'\(?\d{1,4}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}'
    phone = re.search(phone_pattern, text)
    return phone.group(0) if phone else None

def extract_paragraphs(text):
    return re.split(r'\n{2,}', text)

def extract_job_post_info(text):
    paragraphs = extract_paragraphs(text)

    job_title = extract_job_title(text)
    company_name = paragraphs[0].strip() if paragraphs else None

    job_location, job_type, job_description, job_requirements, preferred_qualifications = None, None, None, None, None
    skills, responsibilities, salary_range, benefits = None, None, None, None
    application_deadline, application_instructions, contact_information = None, None, None
    company_culture, equal_opportunity_statement, career_growth_opportunities = None, None, None
    work_schedule, remote_work_options = None, None

    for para in paragraphs:
        if re.search(r'\blocation\b', para, re.IGNORECASE):
            job_location = para.strip()
        elif re.search(r'\b(full-time|part-time|temporary|contract|freelance)\b', para, re.IGNORECASE):
            job_type = para.strip()
        elif re.search(r'\b(salary|compensation)\b', para, re.IGNORECASE):
            salary_range = para.strip()
        elif re.search(r'\b(deadline|closing date)\b', para, re.IGNORECASE):
            application_deadline = para.strip()
        elif re.search(r'\b(remote work|telecommute|work from home)\b', para, re.IGNORECASE):
            remote_work_options = para.strip()
        elif re.search(r'\b(equal opportunity|EEO|EEOC)\b', para, re.IGNORECASE):
            equal_opportunity_statement = para.strip()
        elif re.search(r'\b(responsibilities|duties|tasks)\b', para, re.IGNORECASE):
            responsibilities = para
            strip()
        elif re.search(r'\b(skills|qualifications|requirements)\b', para, re.IGNORECASE):
            if job_requirements is None:
                job_requirements = para.strip()
            elif preferred_qualifications is None:
                preferred_qualifications = para.strip()
        elif re.search(r'\b(benefits|perks)\b', para, re.IGNORECASE):
            benefits = para.strip()
        elif re.search(r'\b(work schedule|working hours)\b', para, re.IGNORECASE):
            work_schedule = para.strip()
        elif re.search(r'\b(culture|values|mission)\b', para, re.IGNORECASE):
            company_culture = para.strip()
        elif re.search(r'\b(career growth|advancement opportunities)\b', para, re.IGNORECASE):
            career_growth_opportunities = para.strip()
        elif re.search(r'\b(instructions|how to apply)\b', para, re.IGNORECASE):
            application_instructions = para.strip()
        elif job_description is None:
            job_description = para.strip()

    email = extract_email(text)
    phone = extract_phone(text)
    contact_information = {'email': email, 'phone': phone}

    return JobPost(job_title, company_name, job_location, job_type, job_description,
                   job_requirements, preferred_qualifications, skills, responsibilities,
                   salary_range, benefits, application_deadline, application_instructions,
                   contact_information, company_culture, equal_opportunity_statement,
                   career_growth_opportunities, work_schedule, remote_work_options)

if __name__ == "__main__":
    job_post_text = """
    # Add your plain text job post here.
    """
    job_post = extract_job_post_info(job_post_text)
    print(job_post)
