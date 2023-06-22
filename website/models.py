from django.utils import timezone
from django.db import models
from django.conf import settings
from hashid_field import HashidAutoField
from django.urls import reverse
from website.utils import h_encode
from django.db import models
from django.utils.text import slugify
from bs4 import BeautifulSoup
import requests
from functools import lru_cache


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True





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
    

from django.db import models
from django.contrib.auth.models import User

class Company(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='company_logos', blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    number_of_employees_min = models.IntegerField(blank=True, null=True)
    number_of_employees_max = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    website_status = models.IntegerField(null=True, blank=True)
    website_status_updated = models.DateTimeField(null=True, blank=True)
    city = models.CharField(max_length=255,blank=True, null=True)
    state = models.CharField(max_length=255,blank=True, null=True)
    country = models.CharField(max_length=255,blank=True, null=True)
    ceo = models.CharField(max_length=255,blank=True, null=True)
    ceo_twitter = models.URLField(blank=True, null=True)
    greenhouse_url = models.URLField(blank=True, null=True)
    wellfound_url = models.URLField(blank=True, null=True)
    lever_url = models.URLField(blank=True, null=True)
    careers_url = models.URLField(blank=True, null=True)
    careers_url_status = models.IntegerField(null=True, blank=True)
    careers_url_status_updated = models.DateTimeField(null=True, blank=True)
    email = models.EmailField(blank=True, null=True)

    greenhouse_icon = '<svg height="2500" viewBox="-8.30925739 -.2362298 217.94925739 445.3362298" width="1269" xmlns="http://www.w3.org/2000/svg"><path d="m104.42 444.2c-58.12.85-105.51-49-104.42-106.6a105.12 105.12 0 0 1 105.87-103.37c55.36.15 101.71 47.66 102.71 103.07 1.06 58.7-47.33 107.8-104.16 106.9zm85.45-104.32c.35-47.58-37.69-86.42-85-86.78s-85.87 37.9-86.27 85.47a86.24 86.24 0 0 0 85.26 87.16c46.79.59 85.66-38.21 86.01-85.85zm-189.66-213.65a86.13 86.13 0 0 1 86-86.83c47.2-.09 86.08 38.89 86.15 86.36.08 48.15-38.19 87.13-85.67 87.27-48.18.13-86.34-38.19-86.48-86.8zm18.91-.54a67 67 0 1 0 134.09 1.31c.24-37.53-29.46-68.13-66.4-68.43-37.13-.26-67.4 29.74-67.69 67.12zm117.97-108.37a17.61 17.61 0 0 1 35.22.24 17.53 17.53 0 0 1 -17.74 17.72c-9.9-.07-17.48-7.87-17.48-17.96z" fill="#38b2a7"/></svg>' # Replace with your actual SVG code
    wellfound_icon = "<svg>...</svg>"  # Replace with your actual SVG code
    lever_icon = "<svg>...</svg>"  # Replace with your actual SVG code


    class Meta:
        verbose_name_plural = "companies"


    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


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
    title = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, blank=True, null=True)
    slug = models.SlugField(unique=True, max_length=255)
    description_markdown = models.TextField(blank=True, null=True)
    job_type = models.CharField(max_length=100)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    posted_date = models.DateField(blank=True, null=True)
    closing_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    link = models.URLField()
    link_status_code = models.IntegerField(null=True, blank=True, default=200)

    equity_min = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    equity_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)


    # @property
    # @lru_cache(maxsize=None)
    # def job_display(self):
    #     if self.role:
    #         return self.role.title + " at " + self.company.name
    #     else:
    #         if self.title:
    #             return self.title + " at " + self.company.name
    #         else:
    #             return self.slug + " at " + self.company.name

    # def __str__(self):
    #     return self.job_display

    def save(self, *args, **kwargs):
        # if not self.title and self.link:
        #     response = requests.get(self.link)
        #     self.link_status_code = response.status_code
        #     soup = BeautifulSoup(response.content, 'html.parser')
        #     self.title = soup.title.string
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class Stage(models.Model):
    name = models.CharField(max_length=255)
    order = models.IntegerField()

    def __str__(self):
        return self.name  

class Email(models.Model):
    from_email = models.CharField(max_length=255)
    to_email = models.CharField(max_length=255, blank=True, null=True)
    reply_to = models.CharField(max_length=255, blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    gmail_id = models.CharField(max_length=255)
    application = models.ForeignKey('Application', on_delete=models.CASCADE, blank=True, null=True)
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
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE,blank=True, null=True)
    date_of_last_email = models.DateTimeField(blank=True, null=True)
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recruiter",
        blank=True, null=True
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


class Source(models.Model):
    name = models.CharField(max_length=255)
    website = models.URLField()
    focus = models.CharField(max_length=255,blank=True, null=True)
    from_email = models.EmailField(blank=True, null=True)
    url_structure = models.TextField(blank=True, null=True)
    job_count = models.PositiveIntegerField(default=0,blank=True, null=True)

    def __str__(self):
        return self.name
    
# User:

# first_name
# last_name
# email
# password
# user_type (job seeker, company, recruiter)

# UserProfile:

# Resume
# Skills at position
# Job SeekerProfile:

# user (OneToOneField with User)
# skills (ManyToManyField with Skill)
# experience (TextField)
# education (TextField)
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
# Skill:

# name
# description
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


# class JobSeeker(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)

# class Experience(models.Model):
#     job_seeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE)
#     company_name = models.CharField(max_length=255)
#     position = models.CharField(max_length=255)
#     start_date = models.DateField()
#     end_date = models.DateField()
#     skills = models.ManyToManyField('Skill')



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
