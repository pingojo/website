from django.db import models
from django.conf import settings
from hashid_field import HashidAutoField
from django.urls import reverse
from website.utils import h_encode
from django.db import models
from django.utils.text import slugify
from bs4 import BeautifulSoup
import requests

class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True





class Skill(BaseModel):
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
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    ceo = models.CharField(max_length=255)
    ceo_twitter = models.URLField(blank=True, null=True)
    greenhouse_url = models.URLField(blank=True, null=True)
    wellfound_url = models.URLField(blank=True, null=True)
    lever_url = models.URLField(blank=True, null=True)
    careers_url = models.URLField(blank=True, null=True)
    careers_url_status = models.IntegerField(null=True, blank=True)
    careers_url_status_updated = models.DateTimeField(null=True, blank=True)

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
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("role-detail", args=[self.slug])
    
class Job(models.Model):
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
    equity_min = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    equity_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)


    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.title and self.link:
            response = requests.get(self.link)
            soup = BeautifulSoup(response.content, 'html.parser')
            self.title = soup.title.string
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class Stage(models.Model):
    name = models.CharField(max_length=255)
    order = models.IntegerField()

    def __str__(self):
        return self.name  

class Email(models.Model):
    email_id = models.CharField(max_length=255)

    def __str__(self):
        return self.email_id
    

class Application(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    date_applied = models.DateField(auto_now_add=True)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE,blank=True, null=True)
    date_of_last_email = models.DateField(blank=True, null=True)
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recruiter",
        blank=True, null=True
    )
    email = models.ForeignKey(Email, on_delete=models.CASCADE, blank=True, null=True)
    def __str__(self):
        return f"{self.company_name} - {self.job_title}"
    
    def get_hashid(self):
        return h_encode(self.id)

    def get_absolute_url(self):
        return reverse("application-detail", args=[self.id])
    



class Search(BaseModel):
    query = models.CharField(max_length=255)
    matched_job_count = models.IntegerField(blank=True, null=True)
    matched_company_count = models.IntegerField(blank=True, null=True)
    matched_skill_count = models.IntegerField(blank=True, null=True)
    matched_role_count = models.IntegerField(blank=True, null=True)


    def __str__(self):
        return self.query


class Source(models.Model):
    name = models.CharField(max_length=255)
    website = models.URLField()
    url_structure = models.TextField()
    job_count = models.PositiveIntegerField(default=0)

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


# from django.db import models
# from django.contrib.auth.models import User

# class JobSeeker(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     skills = models.ManyToManyField('Skill')

# class Company(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     name = models.CharField(max_length=255)
#     contact_info = models.TextField()



# class Application(models.Model):
#     job_seeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE)
#     job = models.ForeignKey(Job, on_delete=models.CASCADE)
#     recruiter = models.ForeignKey(User, on_delete=models.CASCADE)
#     status = models.CharField(max_length=255)
#     adjusted_commission = models.DecimalField(max_digits=6, decimal_places=2)

# class Recruiter(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     total_earnings = models.DecimalField(max_digits=10, decimal_places=2)

# class Skill(models.Model):
#     name = models.CharField(max_length=255)

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


# from django.db import models
# from django.contrib.auth.models import User

# class JobSeeker(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)

# class Experience(models.Model):
#     job_seeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE)
#     company_name = models.CharField(max_length=255)
#     position = models.CharField(max_length=255)
#     start_date = models.DateField()
#     end_date = models.DateField()
#     skills = models.ManyToManyField('Skill')

# class Company(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     name = models.CharField(max_length=255)
#     contact_info = models.TextField()


# class Application(models.Model):
#     job_seeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE)
#     job = models.ForeignKey(Job, on_delete=models.CASCADE)
#     recruiter = models.ForeignKey(User, on_delete=models.CASCADE)
#     status = models.CharField(max_length=255)
#     adjusted_commission = models.DecimalField(max_digits=6, decimal_places=2)

# class Recruiter(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     total_earnings = models.DecimalField(max_digits=10, decimal_places=2)

# class Skill(models.Model):
#     name = models.CharField(max_length=255)

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
