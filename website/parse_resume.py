import PyPDF2
import re
import nltk
from collections import namedtuple

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

# Structured variables
Resume = namedtuple('Resume', ['contact_info', 'objective', 'experience', 'skills'])

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfFileReader(file)
        text = ''
        for page in range(pdf_reader.numPages):
            text += pdf_reader.getPage(page).extractText()
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

    # Customize this list according to the skills you want to extract
    skill_set = {'Python', 'Java', 'C++', 'JavaScript', 'React', 'Node.js', 'SQL', 'HTML', 'CSS'}

    for skill in skill_set:
        if re.search(r'\b' + skill + r'\b', text, re.IGNORECASE):
            skills.append(skill)
    return skills

def extract_experience(text):
    experience = []
    pattern = re.compile(r'(?:\d{1,2}[/|-]\d{4}|[A-Za-z]*\s\d{4})\s*[-|–|to]+\s*(?:\d{1,2}[/|-]\d{4}|[A-Za-z]*\s\d{4}|Present|present)', re.IGNORECASE)

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

def parse_resume(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    contact_info = extract_contact_info(text)
    objective = extract_objective(text)
    experience = extract_experience(text)
    skills = extract_skills(text)

    return Resume(contact_info, objective, experience, skills)

if __name__ == "__main__":
    pdf_path = "path/to/your/resume.pdf"
    resume = parse_resume(pdf_path)
    print(resume)
