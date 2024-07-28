from hashids import Hashids
from django.conf import settings

hashids = Hashids(settings.HASHID_FIELD_SALT, min_length=8)
import requests
import bs4
from django.utils.text import slugify
import re
import docx2txt
from pdfminer.high_level import extract_text
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


def h_encode(id):
    return hashids.encode(id)


def h_decode(h):
    z = hashids.decode(h)
    if z:
        return z[0]


class HashIdConverter:
    regex = "[a-zA-Z0-9]{8,}"

    def to_python(self, value):
        return h_decode(value)

    def to_url(self, value):
        return h_encode(value)


def get_website_title(external_sites_url):
    try:
        r = requests.get("http://" + external_sites_url, timeout=5)
        html = bs4.BeautifulSoup(r.text, features="html.parser")
        title_tag = html.title
        if title_tag:
            return title_tag.text
        else:
            return "No title found"
    except Exception as e:
        return str(e)



def get_text_from_file(file):
    text = ''
    if file.name.endswith('.pdf'):
        text = extract_text(file)
    elif file.name.endswith('.docx'):
        text = docx2txt.process(file)
    else:
        raise ValueError('Unsupported file format')

    return text

def calculate_match_percentage(resume_text, job_description_text):
    resume_text = re.sub(r'\W+', ' ', resume_text.lower())
    job_description_text = re.sub(r'\W+', ' ', job_description_text.lower())

    resume_words = word_tokenize(resume_text)
    job_description_words = word_tokenize(job_description_text)

    stop_words = set(stopwords.words('english'))
    filtered_resume_words = [word for word in resume_words if word not in stop_words]
    filtered_job_description_words = [word for word in job_description_words if word not in stop_words]

    common_words = set(filtered_resume_words).intersection(filtered_job_description_words)

    match_percentage = (len(common_words) / len(set(filtered_job_description_words))) * 100

    return round(match_percentage, 2)


import requests
from django.conf import settings

def send_slack_notification(search):
    slack_webhook_url = settings.SLACK_WEBHOOK_URL
    message = f"{search.query}: {search.matched_job_count}"

    payload = {
        "text": message,
        "channel": "#searches",
        "username": "Search Bot",
        "icon_emoji": ":mag:"
    }

    response = requests.post(slack_webhook_url, json=payload)
    return response.status_code