import requests
from bs4 import BeautifulSoup

sites = [
    'https://www.indeed.com/jobs?q=django&l=',
    'https://www.glassdoor.com/Job/jobs.htm?sc.keyword=django',
    'https://angel.co/jobs#find/f!%7B%22roles%22%3A%5B%22Software%20Engineer%22%5D%2C%22keywords%22%3A%5B%22django%22%5D%7D',
    'https://remoteok.io/remote-django-jobs',
    'https://weworkremotely.com/remote-jobs/search?term=django',
]

for site in sites:
    response = requests.get(site)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    if site == 'https://www.indeed.com/jobs?q=django&l=':
        jobs = soup.find_all('div', class_='jobsearch-SerpJobCard')
        for job in jobs:
            title = job.find('h2', class_='title')
            if title:
                print(title.text.strip())
                
    elif site == 'https://www.glassdoor.com/Job/jobs.htm?sc.keyword=django':
        jobs = soup.find_all('li', class_='react-job-listing')
        for job in jobs:
            title = job.find('a', class_='jobLink')
            if title:
                print(title.text.strip())
                
    elif site == 'https://angel.co/jobs#find/f!%7B%22roles%22%3A%5B%22Software%20Engineer%22%5D%2C%22keywords%22%3A%5B%22django%22%5D%7D':
        jobs = soup.find_all('div', class_='job')
        for job in jobs:
            title = job.find('div', class_='title')
            if title:
                print(title.text.strip())
                
    elif site == 'https://remoteok.io/remote-django-jobs':
        jobs = soup.find_all('tr', class_='job')
        for job in jobs:
            title = job.find('h2', itemprop='title')
            if title:
                print(title.text.strip())
                
    elif site == 'https://weworkremotely.com/remote-jobs/search?term=django':
        jobs = soup.find_all('li', class_='feature')
        for job in jobs:
            title = job.find('span', class_='title')
            if title:
                print(title.text.strip())