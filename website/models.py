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

class Job(models.Model):
    title = models.CharField(max_length=255)
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
    def __str__(self):
        return f"{self.company_name} - {self.job_title}"
    
    def get_hashid(self):
        return h_encode(self.id)

    def get_absolute_url(self):
        return reverse("application-detail", args=[self.id])
    

class Email(models.Model):
    email_id = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return self.email_id