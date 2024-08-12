import re
from functools import lru_cache
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from website.utils import h_encode


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Link(BaseModel):
    url = models.URLField()
    title = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        if self.title:
            return self.title
        else:
            return self.url


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    resume = models.FileField(upload_to="resumes", blank=True, null=True)
    skills = models.ManyToManyField("Skill", related_name="profiles", blank=True)
    roles = models.ManyToManyField("Role", related_name="profiles", blank=True)
    links = models.ManyToManyField("Link", related_name="profiles", blank=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures", blank=True, null=True
    )
    resume_views = models.PositiveIntegerField(default=0)
    web_views = models.PositiveIntegerField(default=0)
    resume_download_count = models.PositiveIntegerField(default=0)
    resume_download_limit = models.PositiveIntegerField(default=0)
    is_public = models.BooleanField(default=True)
    html_resume = models.TextField(blank=True, null=True)
    resume_key = models.URLField(blank=True, null=True)

    # location = models.CharField(max_length=255, blank=True, null=True)
    # website = models.URLField(blank=True, null=True)
    # website_status = models.IntegerField(null=True, blank=True)
    # website_status_updated = models.DateTimeField(null=True, blank=True)
    # twitter_url = models.URLField(blank=True, null=True)
    # linkedin_url = models.URLField(blank=True, null=True)
    # github_url = models.URLField(blank=True, null=True)
    # portfolio_url = models.URLField(blank=True, null=True)
    # portfolio_url_status = models.IntegerField(null=True, blank=True)
    # portfolio_url_status_updated = models.DateTimeField(null=True, blank=True)
    # email = models.EmailField(blank=True, null=True)
    # phone = models.CharField(max_length=255,blank=True, null=True)

    # when saving the profile, if there is html_resume content and no resume_key then generate a new resume_key using YYYYMMDD-X where X is the number of resumes the system has generated that day
    def save(self, *args, **kwargs):
        if not self.resume_key and self.html_resume:
            today = timezone.now().strftime("%Y%m%d")
            self.resume_key = f"{today}-{Profile.objects.filter(created__date=today).count() + 1}"
        super().save(*args, **kwargs)


class Prompt(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()


class Skill(models.Model):
    companies = models.ManyToManyField("Company", related_name="skills")
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="skills")
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    job_count = models.PositiveIntegerField(default=0)
    resume_count = models.PositiveIntegerField(default=0)
    web_views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("skill-detail", args=[self.slug])


class Company(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to="company_logos", blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    number_of_employees_min = models.IntegerField(blank=True, null=True)
    number_of_employees_max = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    website_status = models.IntegerField(null=True, blank=True)
    website_status_updated = models.DateTimeField(null=True, blank=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    ceo = models.CharField(max_length=255, blank=True, null=True)
    ceo_twitter = models.URLField(blank=True, null=True)
    greenhouse_url = models.URLField(blank=True, null=True)
    wellfound_url = models.URLField(blank=True, null=True)
    lever_url = models.URLField(blank=True, null=True)
    careers_url = models.URLField(blank=True, null=True)
    careers_url_status = models.IntegerField(null=True, blank=True)
    careers_url_status_updated = models.DateTimeField(null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    screenshot = models.ImageField(
        upload_to="company_screenshots", blank=True, null=True
    )
    greenhouse_icon = '<svg height="2500" viewBox="-8.30925739 -.2362298 217.94925739 445.3362298" width="1269" xmlns="http://www.w3.org/2000/svg"><path d="m104.42 444.2c-58.12.85-105.51-49-104.42-106.6a105.12 105.12 0 0 1 105.87-103.37c55.36.15 101.71 47.66 102.71 103.07 1.06 58.7-47.33 107.8-104.16 106.9zm85.45-104.32c.35-47.58-37.69-86.42-85-86.78s-85.87 37.9-86.27 85.47a86.24 86.24 0 0 0 85.26 87.16c46.79.59 85.66-38.21 86.01-85.85zm-189.66-213.65a86.13 86.13 0 0 1 86-86.83c47.2-.09 86.08 38.89 86.15 86.36.08 48.15-38.19 87.13-85.67 87.27-48.18.13-86.34-38.19-86.48-86.8zm18.91-.54a67 67 0 1 0 134.09 1.31c.24-37.53-29.46-68.13-66.4-68.43-37.13-.26-67.4 29.74-67.69 67.12zm117.97-108.37a17.61 17.61 0 0 1 35.22.24 17.53 17.53 0 0 1 -17.74 17.72c-9.9-.07-17.48-7.87-17.48-17.96z" fill="#38b2a7"/></svg>'  # Replace with your actual SVG code
    wellfound_icon = "<svg>...</svg>"  # Replace with your actual SVG code
    lever_icon = "<svg>...</svg>"  # Replace with your actual SVG code
    phone = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name[:50])
        super().save(*args, **kwargs)


class RequestLog(BaseModel):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    email = models.EmailField()
    applications = models.PositiveIntegerField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    referer = models.URLField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile.user.username} - {self.company.name}"
class BouncedEmail(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    email = models.EmailField()
    reason = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email


class Role(BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    job_count = models.PositiveIntegerField(default=0)
    resume_count = models.PositiveIntegerField(default=0)
    web_views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title[:50])
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("role-detail", args=[self.slug])


class Job(BaseModel):
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, blank=True, null=True)
    slug = models.SlugField(unique=True, max_length=255)
    description_markdown = models.TextField(blank=True, null=True)
    job_type = models.CharField(max_length=100)
    salary_min = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    salary_max = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    posted_date = models.DateField(blank=True, null=True)
    closing_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    link = models.URLField()
    link_status_code = models.IntegerField(null=True, blank=True, default=200)
    location = models.CharField(max_length=255, blank=True, null=True)
    equity_min = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    equity_max = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    remote = models.BooleanField(null=True, blank=True)

    search_vector = SearchVectorField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        indexes = [GinIndex(fields=["search_vector"])]


from django.db import connection
from django.db.models.signals import post_save
from django.dispatch import receiver

from website.models import Job


@receiver(post_save, sender=Job)
def update_search_vector(sender, instance, **kwargs):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE website_job
            SET search_vector = 
                setweight(to_tsvector('english', coalesce(website_role.title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(description_markdown, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(website_company.name, '')), 'C')
            FROM website_role, website_company
            WHERE website_job.role_id = website_role.id AND
                  website_job.company_id = website_company.id AND
                  website_job.id = %s
        """,
            [instance.id],
        )


class Stage(models.Model):
    name = models.CharField(max_length=255)
    order = models.IntegerField()

    def __str__(self):
        return self.name


class Email(models.Model):
    # add user here
    gmail_id = models.CharField(max_length=255)
    application = models.ForeignKey(
        "Application", on_delete=models.CASCADE, blank=True, null=True
    )
    date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.gmail_id


class Application(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    date_applied = models.DateTimeField(auto_now_add=True)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, blank=True, null=True)
    date_of_last_email = models.DateTimeField(blank=True, null=True)
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recruiter",
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.company.name} - {self.job.slug}"

    def get_hashid(self):
        return h_encode(self.id)

    def get_absolute_url(self):
        return reverse("application-detail", args=[self.id])

    def days_since_last_email(self):
        if self.date_of_last_email:
            return (timezone.now() - self.date_of_last_email).days
        else:
            return None


class Search(BaseModel):
    query = models.CharField(max_length=255)
    matched_job_count = models.IntegerField(blank=True, null=True)
    matched_company_count = models.IntegerField(blank=True, null=True)
    matched_skill_count = models.IntegerField(blank=True, null=True)
    matched_role_count = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Searches"

    def __str__(self):
        return self.query


class Source(BaseModel):
    name = models.CharField(max_length=255)
    website = models.URLField()
    focus = models.CharField(max_length=255, blank=True, null=True)
    from_email = models.EmailField(blank=True, null=True)
    url_structure = models.TextField(blank=True, null=True)
    search_url = models.URLField(default="", blank=True, null=True)
    job_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    google_result_count = models.PositiveIntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return self.name

    def get_google_result_count(self):
        if self.website:
            agent = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"
            }

            response = requests.get(
                "https://www.google.com/search?q=site:" + self.get_domain(),
                headers=agent,
            )
            soup = BeautifulSoup(response.content, "html.parser")
            result_stats = soup.find(id="result-stats")
            if result_stats:
                result_stats = result_stats.text
                number = re.search(r"(\d+)", result_stats.replace(",", ""))
                if number:
                    return int(number.group(0))
                else:
                    return 0
            else:
                return 0
        else:
            return 0

    def get_domain(self):
        domain = urlparse(self.website).netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain

    def save(self, *args, **kwargs):
        if self.google_result_count < 1:
            self.google_result_count = self.get_google_result_count()
        self.job_count = Job.objects.filter(link__icontains=self.get_domain()).count()
        super().save(*args, **kwargs)


# User:
# first_name
# last_name
# email
# password
# user_type (job seeker, company, recruiter)

# UserProfile:
# Resume
# Skills at position


# Company:
# user (OneToOneField with User)
# name
# description
# industry
# location
# website

# RecruiterProfile:
# user (OneToOneField with User)
# rating
# total_matches
# earnings


# Job:
# company (ForeignKey to Company)
# title
# description
# requirements
# location
# salary_range
# job_type (full-time, part-time, contract, etc.)
# posted_date


# Application:
# job (ForeignKey to Job)
# job_seeker (ForeignKey to User with job seeker user_type)
# recruiter (ForeignKey to User with recruiter user_type)
# status (applied, scheduled, passed, etc.)
# applied_date
# last_email_date
# commission_fee
# processing_fee


# Payment:
# payer (ForeignKey to User)
# payee (ForeignKey to User)
# amount
# payment_type (commission_fee, processing_fee, hiring_fee)
# date

# class JobSeeker(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     skills = models.ManyToManyField('Skill')
#     experience (TextField)
#     education (TextField)


# class Recruiter(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     total_earnings = models.DecimalField(max_digits=10, decimal_places=2)

# class Match(models.Model):
#     job_seeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE)
#     job = models.ForeignKey(Job, on_delete=models.CASCADE)
#     recruiter = models.ForeignKey(User, on_delete=models.CASCADE)
#     score = models.FloatField()
#     commission_adjustment = models.DecimalField(max_digits=6, decimal_places=2)

# class DailyEmail(models.Model):
#     company = models.ForeignKey(Company, on_delete=models.CASCADE)
#     content = models.TextField()
#     date_sent = models.DateField()

# class Agreement(models.Model):
#     job_seeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE)
#     company = models.ForeignKey(Company, on_delete=models.CASCADE)
#     terms = models.TextField()
#     contact_info_exchanged = models.BooleanField(default=False)

# class Experience(models.Model):
#     job_seeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE)
#     company = models.CharField(max_length=255)
#     position = models.CharField(max_length=255)
#     start_date = models.DateField()
#     end_date = models.DateField()
#     skills = models.ManyToManyField('Skill')
