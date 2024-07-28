import re
import nltk
from collections import namedtuple
import io
from PyPDF2 import PdfReader
from .models import Skill
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

# Structured variables
#Resume = namedtuple('Resume', ['contact_info', 'objective', 'experience', 'skills'])

Resume = namedtuple('Resume', ['name', 'contact_info', 'objective', 'experience', 'skills', 'education'])


def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PdfReader(pdf_file)
        page = pdf_reader.pages[0]
        text = page.extract_text()
        print("text: ", text)
        return text

def extract_contact_info(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\(?\d{1,4}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}'

    email = re.search(email_pattern, text)
    phone = re.search(phone_pattern, text)

    return {'email': email.group(0) if email else None,
            'phone': phone.group(0) if phone else None}

def extract_skills(text):
    skills = []

    for skill in Skill.objects.all():
        if re.search(r'\b' + re.escape(skill.name) + r'\b', text, re.IGNORECASE):
            skills.append(skill.name)
    return skills


def extract_experience(text):
    experience = []
    pattern = re.compile(r'(?:\d{1,2}[/|-]\d{4}|[A-Za-z]+(?:\s\d{4}))\s*[-|–|to]+\s*(?:\d{1,2}[/|-]\d{4}|[A-Za-z]+(?:\s\d{4})?|Present|present)', re.IGNORECASE)

    for match in pattern.finditer(text):
        experience.append(match.group())

    return experience


def extract_objective(text):
    sentences = nltk.sent_tokenize(text)
    tagged_sentences = nltk.pos_tag(sentences)

    objective = ''
    for i, sentence in enumerate(tagged_sentences):
        if 'VB' in sentence[1] and 'NN' in sentence[1] and i < 5:
            objective = sentences[i]
            break

    return objective

def extract_name(text):
    # Assuming the name is located at the beginning of the resume
    name = text.split('\n')[0].strip()
    return name

def extract_education(text):
    education = []
    # Customize this list according to the education levels you want to extract
    education_levels = ['Bachelor', 'Master', 'Doctor', 'PhD', 'B.Sc', 'M.Sc', 'B.A', 'M.A']

    for edu_level in education_levels:
        # Search for education level followed by the field of study
        pattern = re.compile(r'(' + edu_level + r')\s*[\w\s]*', re.IGNORECASE)
        matches = pattern.findall(text)

        for match in matches:
            if match not in education:
                education.append(match)

    return education


def parse_resume(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    name = extract_name(text)  # Assuming you have a function to extract the name
    contact_info = extract_contact_info(text)
    objective = extract_objective(text)
    experience = extract_experience(text)
    skills = extract_skills(text)
    education = extract_education(text)  # Assuming you have a function to extract education

    return Resume(name, contact_info, objective, experience, skills, education)

# if __name__ == "__main__":
#     pdf_path = "path/to/your/resume.pdf"
#     resume = parse_resume(pdf_path)
#     print(resume)
