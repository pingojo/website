import os
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# URL to scrape jobs from BuiltinNYC
job_url = "https://www.builtinnyc.com/jobs/remote/1-10/11-50?search=python"

# API endpoint and key for Pingojo
PINGOJO_API_URL = "https://api.pingojo.com/jobs"
API_KEY = "your_api_key_here"


def extract_builtinnyc_info(content):
    """Extract job information from BuiltinNYC page content."""
    soup = BeautifulSoup(content, "html.parser")
    jobs = soup.find_all(attrs={"data-id": "job-card"})

    job_listings = []

    for job in jobs:
        title_tag = job.find("h2", class_="fw-extrabold fs-md fs-xl-xl")
        company_div = job.find("div", attrs={"data-id": "company-title"})
        job_link_tag = title_tag.find("a") if title_tag else None
        company_logo_tag = job.find("img", attrs={"data-id": "company-img"})
        time_posted_tag = job.find("span", class_="font-barlow text-gray-03")
        job_type_tags = job.find_all("span", class_="font-barlow text-gray-03")
        employees_tag = job.find("span", string=re.compile(r"Employees"))
        experience_tag = job.find("span", string=re.compile(r"Years of Experience"))
        description_tag = job.find("div", class_="fs-xs fw-regular mb-md")
        benefits_tags = job.find_all("div", class_="font-barlow fs-md text-gray-03")

        title = job_link_tag.text.strip() if job_link_tag else "Unknown"
        company = (
            company_div.find("span").text.strip()
            if company_div and company_div.find("span")
            else "Unknown"
        )
        job_link = (
            f"https://www.builtinnyc.com{job_link_tag['href']}"
            if job_link_tag and "href" in job_link_tag.attrs
            else "Unknown"
        )
        company_logo = (
            company_logo_tag["src"]
            if company_logo_tag and "src" in company_logo_tag.attrs
            else "Unknown"
        )
        time_posted = time_posted_tag.text.strip() if time_posted_tag else "Unknown"
        job_type = ", ".join(
            [
                tag.text.strip()
                for tag in job_type_tags
                if tag and tag.text.strip() in ["Remote", "Hybrid"]
            ]
        )
        employees = employees_tag.text.strip() if employees_tag else "Unknown"
        experience = experience_tag.text.strip() if experience_tag else "Unknown"
        description = description_tag.text.strip() if description_tag else "Unknown"
        benefits = ", ".join([tag.text.strip() for tag in benefits_tags])

        job_listings.append(
            {
                "title": title,
                "company": company,
                "job_link": job_link,
                "company_logo": company_logo,
                "time_posted": time_posted,
                "job_type": job_type,
                "employees": employees,
                "experience": experience,
                "description": description,
                "benefits": benefits,
            }
        )

    return job_listings


def extract_job_info(url):
    """Extract job info from BuiltinNYC."""
    response = requests.get(url)
    if response.status_code == 200:
        return extract_builtinnyc_info(response.content)
    else:
        print(
            f"Failed to retrieve content from {url}. Status code: {response.status_code}"
        )
        return []


def post_to_pingojo(job_info):
    """Post job information to Pingojo."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    for job in job_info:
        response = requests.post(PINGOJO_API_URL, headers=headers, json=job)
        if response.status_code == 201:
            print(f"Successfully posted job: {job['title']} at {job['company']}")
        else:
            print(
                f"Failed to post job: {job['title']} at {job['company']}. Status code: {response.status_code}, Response: {response.text}"
            )


def main():
    print(f'Scraping URL: "{job_url}"')
    job_info = extract_job_info(job_url)
    print("Job info extracted:")
    for job in job_info:
        print(job.get("company"), job.get("title"))

    # print(job_info)
    # post_to_pingojo(job_info)


if __name__ == "__main__":
    main()
