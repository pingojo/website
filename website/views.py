import os
import random
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from django.forms import DurationField

import requests
from bs4 import BeautifulSoup
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import models
from django.db.models import (Case, CharField, Count, DateField, F,
                              IntegerField, Prefetch, Q, Sum, Value, When)
from django.db.models.functions import Cast, Coalesce, Concat, TruncDay
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
# views.py
# from pyresparser import ResumeParser
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views import View, generic
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from website.models import Application, Company, Email, Job, Role, Stage
from website.utils import get_website_title, send_slack_notification

from .forms import CompanyUpdateForm, JobForm, ResumeUploadForm
from .models import (Application, Company, Email, Job, Role, Search, Skill,
                     Source, Stage)
from .parse_resume import parse_resume
#from .forms import ChallengeForm
from .utilities import send_challenge_email

from django.db.models import F, Value, DateTimeField
from django.db.models.functions import Coalesce, Cast, ExtractDay
from django.utils import timezone

from django.db.models import F, ExpressionWrapper, fields
from django.db.models.functions import Coalesce
from django.utils import timezone

from django.utils.duration import _get_duration_components
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from datetime import timedelta

from django.contrib.auth.models import User
from selenium.common.exceptions import TimeoutException

# import min and max
from django.db.models import Min, Max

from django.conf import settings

from django.db import models
from django.utils import timezone

class CustomDurationField(models.DurationField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        return timezone.timedelta(seconds=value.total_seconds()).days

from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from .models import Company
from django.contrib.sessions.models import Session

import re
from django.http import JsonResponse

from .models import Company, Role, Job

import logging
from django.core.cache import cache


logger = logging.getLogger(__name__)

# def generage_follow_up_email(request, application_id):
#     application = get_object_or_404(Application, pk=application_id)
#     company_name = application.company.name
#     date_applied = application.date_applied.strftime('%-m/%-d')
#     role = application.job.role.title if application.job.title else "[role]"
#     email = application.company.email
#     email_subject = f"Follow up on {role} role at {company_name}"
#     email_body = f"Hi {company_name},\n\nI hope you are doing well. " \
#                  f"I wanted to follow up on my application for the {role} " \
#                  f"role at {company_name} that I submitted on {date_applied}. " \
#                  f"I am very interested in the role and would like to learn " \
#                  f"more about the opportunity. Please let me know if you have " \
#                  f"any questions or if there is anything else I can provide.\n\n" \
#                  f"Thanks,\n\n{request.user.first_name} {request.user.last_name}"
#     return redirect(f"https://mail.google.com/mail/?view=cm&fs=1&to={email}" \
#                     f"&su={email_subject}&body={email_body}")


#reqired login

@login_required
def update_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == 'POST':
        #job.title = request.POST.get('title')
        #job.description = request.POST.get('description')
        if not job.role:
            role = request.POST.get('role')
            if role:
                role_slug = slugify(role[:50])
                role, _ = Role.objects.get_or_create(
                    slug=role_slug, defaults={"title": role}
                )
                job.role = role
                job.save()

                webhook_url = settings.SLACK_WEBHOOK_URL
        
                if webhook_url:
                    message = f"{job.company.name} updated to {role.title}"
                    payload = {
                        "text": message,
                        "channel": "#updates",
                        "username": "Job Update",
                        "icon_emoji": ":tada:"
                    }
                    requests.post(webhook_url, json=payload)
                return HttpResponse(role)

    return JsonResponse({'success': False})

@login_required
def update_company(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        email = request.POST.get('email')
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return JsonResponse({'success': False, 'error': 'Invalid email address'})
        
        if not company.email:
            company.email = email or company.email
        
        if not company.twitter_url:
            company.twitter_url = request.POST.get('twitter_url') or company.twitter_url
        
        if not company.number_of_employees_min:
            company.number_of_employees_min = request.POST.get('number_of_employees_min') or company.number_of_employees_min
        
        if not company.number_of_employees_max:
            company.number_of_employees_max = request.POST.get('number_of_employees_max') or company.number_of_employees_max
        
        if not company.description:
            company.description = request.POST.get('description') or company.description
        
        if not company.website:
            company.website = request.POST.get('website') or company.website
        
        if not company.city:
            company.city = request.POST.get('city') or company.city
        
        if not company.state:
            company.state = request.POST.get('state') or company.state
        
        if not company.country:
            company.country = request.POST.get('country') or company.country
        
        if not company.ceo:
            company.ceo = request.POST.get('ceo') or company.ceo
        
        if not company.ceo_twitter:
            company.ceo_twitter = request.POST.get('ceo_twitter') or company.ceo_twitter

        company.save()

        webhook_url = settings.SLACK_WEBHOOK_URL
        
        if webhook_url:
            message = f"{company.name} updated:" + str(request.POST)
            payload = {
                "text": message,
                "channel": "#updates",
                "username": "Company Update",
                "icon_emoji": ":tada:"
            }
            requests.post(webhook_url, json=payload)

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request'})
    
# def challenge(request):
#     if request.method == 'POST':
#         form = ChallengeForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data['email']
#             # you would need to get these details from your data
#             from_name = 'your_name'
#             applications_count = 'your_applications_count'
#             send_challenge_email(email, from_name, applications_count)
#             # return a success message or redirect as per your app design
#     else:
#         form = ChallengeForm()
#     return render(request, 'challenge.html', {'form': form})



# def job_add(request):
#     if request.method == 'POST':
#         form = JobForm(request.POST)
#         if form.is_valid():
#             job = form.save(commit=False)
#             job.user = request.user
#             # job.company = form.cleaned_data['company_name']
#             # job.role = form.cleaned_data['role_title']
#             job.save()

#             return JsonResponse({'success': True, 'job_id': job.id})
#         else:
#             return JsonResponse({'success': False, 'errors': form.errors})
#     else:
#         form = JobForm()
#     return render(request, 'job_add.html', {'form': form})


def update_email(request):
    if request.method == "POST":
        application = get_object_or_404(Application, pk=request.POST.get("application_id", None))

        new_email = request.POST.get("email", None)
        if new_email:
            regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            if not re.match(regex, new_email):
                return JsonResponse({'error': 'Invalid email address'}, status=400)
            
            if application.user == request.user and new_email:
                application.job.company.email = new_email
                application.job.company.save()
                application.job.company.refresh_from_db()
                return render(request, 'partials/email.html', {
                    'application': application,
                })
        new_role = request.POST.get("role", None)
        
        if new_role:
            role_slug = slugify(new_role[:50])
            role, _ = Role.objects.get_or_create(
                slug=role_slug, defaults={"title": new_role}
            )
            application.job.role = role
            application.job.save()
            return HttpResponse(new_role)
        
    return JsonResponse({'error': 'Invalid Method or Missing email field'}, status=400)



class JobListView(ListView):
    model = Job
    template_name = 'job_list.html'
    context_object_name = 'jobs'
    paginate_by = 50

    def get_queryset(self):
        if self.request.GET.get('view') == "grid":
            self.template_name = "job_list_grid.html"
        else:
            self.template_name = "job_list_table.html"
        jobs = Job.objects.all().only('company', 'role', 'salary_min', 'salary_max', 'posted_date', 'created', 'link', 'link_status_code' ).select_related('company', 'role').order_by(self.request.GET.get('ordering', '-posted_date'))
        if self.request.GET.get("apply_by_email", ""):
            print("apply by email")
            # filter jobs that have company_email set
            jobs = jobs.filter(company__email__isnull=False)
        return jobs
    
    # def get_ordering(self):
    #     self.ordering = self.request.GET.get('ordering', '-posted_date')
    #     return self.ordering

    # def get_queryset(self):
    #     ordering = self.get_ordering()
    #     direction = '-' if ordering.startswith('-') else ''
    #     field = ordering.lstrip('-')

    #     queryset = super().get_queryset()
    #     queryset = queryset.select_related('company', 'role')
    #     queryset = queryset.annotate(null_dates=Case(
    #         When(posted_date__isnull=True, then=Value(1)),
    #         default=Value(0),
    #         output_field=IntegerField(),
    #     ))
    #     queryset = queryset.order_by('null_dates', f'{direction}{field}')
        
    #     return queryset1



class SourceListView(ListView):
    model = Source
    template_name = 'sources.html'
    context_object_name = 'sources'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        sort = self.request.GET.get('sort', 'google_result_count') 
        direction = self.request.GET.get('direction', 'desc')
        if sort:
            if direction == 'desc':
                sort = '-' + sort
            queryset = queryset.order_by(sort)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', '')
        context['current_direction'] = self.request.GET.get('direction', '')
        return context




class CompanyListView(ListView):
    model = Company
    template_name = 'company_list.html'
    context_object_name = 'companies'
    paginate_by = 100

    def get_queryset(self):
        order = self.request.GET.get('order')
        companies = Company.objects.prefetch_related('application_set')
        # # Use Django's caching system
        # applications = cache.get('applications_queryset')
        
        # if not applications:
        #     if self.request.user.is_authenticated:
        #         applications = Application.objects.select_related('stage').filter(user=self.request.user)
        #     else:
        #         applications = Application.objects.none()
            
        #     # Store the queryset in cache for 5 minutes
        #     cache.set('applications_queryset', applications, 300)

        # # Use Django's caching system
        # companies = cache.get('companies_queryset')
        
        # if not companies:
        #     companies = Company.objects.prefetch_related(Prefetch('application_set', queryset=applications)).annotate(
        #         job_site_order=Case(
        #             When(~Q(greenhouse_url='') & ~Q(greenhouse_url__isnull=True), then=Value(1)),
        #             When(~Q(wellfound_url='') & ~Q(wellfound_url__isnull=True), then=Value(2)),
        #             When(~Q(lever_url='') & ~Q(lever_url__isnull=True), then=Value(3)),
        #             When(~Q(careers_url='') & ~Q(careers_url__isnull=True), then=Value(4)),
        #             default=Value(5),
        #             output_field=IntegerField(),
        #         )
        #     ).order_by('job_site_order')
            
        #     # Store the queryset in cache for 5 minutes
        #     cache.set('companies_queryset', companies, 300)

        if order:
            companies = companies.order_by(order)

        return companies

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     forms = {}
    #     for company in context['companies']:
    #         forms[company.id] = CompanyUpdateForm(instance=company)
    #     context['forms'] = forms
    #     return context

    def post(self, request, *args, **kwargs):
        company_id = request.POST.get('company_id')
        company = get_object_or_404(Company, id=company_id)
        form = CompanyUpdateForm(request.POST, instance=company)

        if form.is_valid():
            form.save()

        # Get the current URL parameters
        order = request.POST.get('order')
        page = request.POST.get('page')

        # Construct the redirect URL with the preserved parameters
        redirect_url = reverse('company_list') + '?'
        if order:
            redirect_url += f'order={order}&'
        if page:
            redirect_url += f'page={page}'

        return HttpResponseRedirect(redirect_url)



    


def autocomplete(request, model):
    term = request.GET.get("term")

    term = "".join(e for e in term if e.isalnum())

    
    if model == "role":
        queryset = Role.objects.filter(title__icontains=term)
        results = [{"label": role.title, "value": role.id} for role in queryset]
    elif model == "company":
        queryset = Company.objects.filter(name__icontains=term)
        results = [{"label": company.name, "value": company.id} for company in queryset]
    else:
        results = []
    return JsonResponse(results, safe=False)


def job_add(request):
    if request.method == "POST":
        form = JobForm(request.POST)
        
        if form.is_valid():
            job = form.save(commit=False)  # Do not save the object to DB just yet
            job.added_by = request.user  # Assign the current user to 'added_by'
            job.slug = slugify(job.role.title + "-at-" + job.company.name)
            job.save()  # Now save it to DB
            messages.success(request, "Job created successfully.")
            return redirect("job_detail", slug=job.slug)
        else:
            print("form errors", form.errors)
            messages.error(request, "The form has errors.")
    else:
        form = JobForm()
    return render(request, "job_add.html", {"form": form})


@login_required
def job_application_delete(request, application_id):
    if request.method == "POST":
        application = get_object_or_404(Application, id=application_id)

        # Check if the application user matches the current user
        if application.user == request.user:
            application.delete()
            return JsonResponse({"status": "success", "application_id": application_id})
        else:
            return JsonResponse({"status": "error", "message": "You are not authorized to delete this application."})


@login_required
def update_application_link(request):
    if request.method == "POST":
        application_id = request.POST.get("application_id")
        link = request.POST.get("link")
        application = get_object_or_404(Application, id=application_id)

        # Check if the application user matches the current user
        if application.user == request.user:
            application.job.link = link
            application.job.save()
            # reload the application.job
            application.job.refresh_from_db()

            # Return an HTML snippet of the updated link, styled green
            return render(request, 'partials/link.html', {
                'application': application,
                'status': 'success'
            })
        else:
            # Return an HTML snippet of the error message, styled red
            return render(request, 'partials/link.html', {
                'application': application,
                'status': 'error',
                'message': 'You are not authorized to update this application.'
            })



def update_application_stage(request):
    if request.method == 'POST':
        application_id = request.POST.get("application_id")
        stage_id = request.POST.get("stage_id")
    elif request.method == 'GET':
        application_id = request.GET.get("application_id")
        stage_id = request.GET.get("stage_id")
    try:
        application = Application.objects.get(pk=application_id)
        stage = Stage.objects.get(pk=stage_id)

        application.stage = stage
        application.save()

        messages.success(request, "Application stage updated successfully.")

        if request.headers.get("HX-Request"):
            return JsonResponse({"status": "success", "application_id": application_id})

    except Application.DoesNotExist:
        messages.error(request, "Application not found.")
    except Stage.DoesNotExist:
        messages.error(request, "Stage not found.")
    except Exception as e:
        messages.error(request, f"Error updating application stage: {e}")

    if request.headers.get("HX-Request"):
        return JsonResponse({"success": False, "message": list(messages.get_messages(request))}, status=400)
    else:
        return redirect("dashboard")


class ResumeUploadView(View):
    def post(self, request, *args, **kwargs):
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume = request.FILES["resume"]
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in resume.chunks():
                    temp_file.write(chunk)
            try:
                resume_data = parse_resume(temp_file.name)
            finally:
                os.unlink(temp_file.name)

            request.session["resume_data"] = resume_data
            return HttpResponseRedirect(reverse("display_resume"))
        else:
            return JsonResponse({"error": "Invalid file."})


class DisplayResumeView(View):
    def get(self, request, *args, **kwargs):
        resume_data = request.session.get("resume_data", None)
        if resume_data:
            del request.session["resume_data"]
            return render(request, "display_resume.html", {"resume_data": resume_data})
        else:
            return HttpResponseRedirect(reverse("upload_resume"))


import re


class AddJobLink(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        company_name = data.get("company","").strip()
        role_title = data.get("title", "").strip()

        posted_date = data.get("datePosted")
        salaryRange = data.get("salaryRange","").strip()
        CompanySalary = data.get("companySalary","").strip()
        if not salaryRange and CompanySalary:
            salaryRange = CompanySalary
        location = data.get("location","").strip()
        website = data.get("website", "").strip()
        country = data.get("companyAddress", "").strip()
        if country and not location:
            location = country
        job_type = data.get("companyStatus", "").strip()
        remote = data.get("companyRemote", "").strip() == "Yes" or True
        CompanyPhone = data.get("companyPhone", "").strip()
        CompanyEmail = data.get("companyEmail", "").strip()
        description = data.get("description", "").strip()



        link = data.get("link")

        # Parse salary range
        salary_min, salary_max = None, None
        if salaryRange:
            salary_values = re.findall(r"\$[\d,]+", salaryRange)
            if len(salary_values) == 2:
                salary_min = int(salary_values[0].replace("$", "").replace(",", ""))
                salary_max = int(salary_values[1].replace("$", "").replace(",", ""))

        if role_title:
            role_slug = slugify(role_title[:50])
            role, _ = Role.objects.get_or_create(
                slug=role_slug, defaults={"title": role_title}
            )
        else:
            role_slug = slugify(data.get("title", "").strip()[:50])
            role, _ = Role.objects.get_or_create(
                slug=role_slug, defaults={"title": data.get("title", "").strip()[:50]}
            )

        company, _ = Company.objects.update_or_create(
            slug=slugify(company_name).strip()[:50], 
            defaults={
                "name": company_name,
                "website": website,
                "country": country,
                "email": CompanyEmail,
                "phone": CompanyPhone,
                }
        )


        job, _ = Job.objects.update_or_create(
            company=company,
            role=role,
            slug=slugify(role.title + "-at-" + company.name),
            defaults={
                "posted_date": posted_date,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "link": link,
                "title": role.title,
                "location": location,
                "job_type": job_type,
                "remote": remote,
                "description_markdown": description,
            },
        )
        user_applications = Application.objects.filter(
            user=request.user, company=company
        )

        application_data = []
        for application in user_applications:
            application_data.append(
                {
                    "id": application.id,
                    "role": application.job.role.title if application.job.role else "",
                    "company": application.company.name,
                    "stage": application.stage.name,
                    "date_applied": application.date_applied,
                }
            )

        return JsonResponse(
            {"applications": application_data}, status=status.HTTP_200_OK
        )


class ApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        emails = (
            Email.objects.filter(application__user=request.user)
            .select_related("application__job__role", "application__company")
            .annotate(
                company_name=F("application__company__name"),
                company_slug=F("application__company__slug"),
                job_link=F("application__job__link"),
                job_role=F("application__job__role__title"),
                stage_name=F("application__stage__name"),
            )
            .values(
                "gmail_id",
                "subject",
                "company_name",
                "company_slug",
                "job_link",
                "job_role",
                "stage_name",
            )
        )

        email_data = list(emails)

        stage_counts = (
            Application.objects.filter(user=request.user)
            .values("stage__name")
            .annotate(total=Count("stage"))
        )

        stage_counts_dict = {
            f'total_{stage["stage__name"].lower()}': stage["total"]
            for stage in stage_counts
        }

        data = {"emails": email_data, "counts": stage_counts_dict}

        return Response(data)

    def post(self, request):
        data = request.data
        company_name = data.get("company_name")
        role_title = data.get("role_title", "").strip()
        email_date_str = data.get("email_date")
        stage_name = data.get("stage_name")
        from_email = data.get("from_email", "").strip()
        gmail_id = data.get("gmail_id")

        role, company, max_stage, job, stage, date_applied, original_date = (None,) * 7

        if role_title:
            role_slug = slugify(role_title[:50])
            role, _ = Role.objects.get_or_create(
                slug=role_slug, defaults={"title": role_title}
            )

        company, _ = Company.objects.get_or_create(
            slug=slugify(company_name), defaults={"name": company_name}
        )

        max_stage = Stage.objects.all().order_by("order").last()
        max_stage = max_stage.order if max_stage else 0

        job, _ = Job.objects.update_or_create(
            company=company,
            role=role,
            slug=slugify(role.title + "-at-" + company.name)
        )

        stage, _ = Stage.objects.get_or_create(
            name=stage_name, defaults={"order": max_stage + 1}
        )

        if stage_name == "Applied":
            try:
                original_date = datetime.strptime(
                    email_date_str, "%a, %b %d, %Y, %I:%M %p"
                )
            except:
                original_date = datetime.strptime(email_date_str, "%b %d, %Y, %I:%M %p")

            original_date = original_date.astimezone().replace(tzinfo=None)
            date_applied = original_date.strftime("%Y-%m-%d %H:%M:%S")

        application, created = Application.objects.get_or_create(
            user=request.user,
            job=job,
            company=company,
            defaults={"stage": stage, "date_applied": date_applied},
        )

        if stage_name in ["Passed", "Next", "Scheduled"]:
            try:
                original_date = datetime.strptime(
                    email_date_str, "%a, %b %d, %Y, %I:%M %p"
                )
            except:
                original_date = datetime.strptime(email_date_str, "%b %d, %Y, %I:%M %p")
            original_date = original_date.astimezone().replace(tzinfo=None)
            application.stage = stage

        if not created and application.date_applied and original_date:
            original_date = timezone.make_aware(
                original_date, timezone.get_current_timezone()
            )

            if application.date_applied > original_date:
                application.date_applied = original_date
        if created:
            original_date = timezone.make_aware(
                original_date, timezone.get_current_timezone()
            )

            if application.date_applied > original_date:
                application.date_applied = original_date

        try:
            email_date = timezone.datetime.strptime(
                email_date_str, "%a, %b %d, %Y, %I:%M %p"
            )
        except:
            email_date = timezone.datetime.strptime(
                email_date_str, "%b %d, %Y, %I:%M %p"
            )

        email_date_aware = timezone.make_aware(
            email_date, timezone.get_current_timezone()
        )

        if application.date_of_last_email:
            if email_date_aware > application.date_of_last_email:
                application.date_of_last_email = email_date_aware
        else:
            application.date_of_last_email = email_date

        if stage.order > application.stage.order:
            application.stage = stage
        application.save()

        if gmail_id:
            from_email = from_email.strip()
            Email.objects.get_or_create(
                gmail_id=gmail_id,
                defaults={
                    "date": email_date,
                    "from_email": from_email,
                    "application": application,
                },
            )

        stage_counts = {}
        for stage in Stage.objects.all():
            stage_counts["total_" + stage.name.lower()] = Application.objects.filter(
                user=request.user, stage=stage
            ).count()

        email_data = {
            "email_id": gmail_id,
            "subject": data.get("subject"),
            "company_name": company_name,
            "company_slug": company.slug,
            "job_link": job.link,
            "job_role": role.title if role else None,
            "stage": stage.name,
        }

        data = {"email": email_data, "counts": stage_counts}

        return JsonResponse(data, status=status.HTTP_201_CREATED)

from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from .models import Job, Application

class JobDetailView(DetailView):
    model = Job
    template_name = "job_detail.html"
    context_object_name = "job"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.get_object()
        if self.request.user.is_authenticated:
            applications = Application.objects.filter(job=job, user=self.request.user)
            context['applications'] = applications
        context["stages"] = Stage.objects.annotate(count=Count('application')).order_by("-order")
        return context

def privacy_policy(request):
    return render(request, "privacy_policy.html")


def terms_of_service(request):
    return render(request, "terms_of_service.html")


def search(request):
    search_query = re.sub(r"[^a-zA-Z0-9,. ]", "", request.GET.get("search", "").strip())   
    
    if search_query:
        jobs = Job.objects.filter(
            Q(title__icontains=search_query) | Q(company__name__icontains=search_query) | Q(description_markdown__icontains=search_query) 
        ).annotate(
            relevance=Case(
                When(title__icontains=search_query, then=Value(2)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by("-relevance")
        companies = Company.objects.filter(Q(name__icontains=search_query) | Q(website__icontains=search_query))
    else:
        jobs = Job.objects.all()
        companies = Company.objects.all()
    if request.GET.get("apply_by_email", ""):
        print("apply by email")
        jobs = jobs.filter(company__email__isnull=False)

    search = Search(
        query=search_query,
        matched_job_count=jobs.count(),
        matched_company_count=companies.count(),
        # matched_skill_count=matched_skill_count,
        # matched_role_count=matched_role_count
    )
    search.save()

    send_slack_notification(search)
    total_jobs = jobs.count()

    jobs_paginator = Paginator(jobs, 50) 
    jobs_page = request.GET.get("jobs_page", 1)

    try:
        jobs_page = int(jobs_page)
    except:
        jobs_page = 1

    paginated_jobs = jobs_paginator.get_page(jobs_page)

    if request.GET.get("view", "") == "grid":
        template = "job_list_grid.html"

    else:
        template = "job_list_table.html"
    return render(
        request,
        template,
        {   
            "page_obj": paginated_jobs,
            "total_jobs": total_jobs,
        },
    )


def scrape_job(request):
    url = request.GET.get("url", "")

    if not "greenhouse" in url and not "lever" in url:
        return JsonResponse({"job_title": "", "company_name": ""})
    
    job_title = ""
    company_name = ""
    return JsonResponse({"job_title": job_title, "company_name": company_name})


from django.utils import timezone


class DashboardView(LoginRequiredMixin, ListView):
    template_name = "dashboard.html"
    context_object_name = "applications"
    paginate_by = 50 # Change this value as per your requirement

    def get_queryset(self):
        stage = self.request.GET.get('stage', 'Scheduled')
        stage_obj = get_object_or_404(Stage, name=stage)

        sort_by = self.request.GET.get("sort_by", "applied")
        sort_order = self.request.GET.get("sort_order", "desc")

        applications = Application.objects.filter(user=self.request.user, stage=stage_obj).prefetch_related("company", "stage", "job", "job__company", "job__role", "email_set").order_by("-stage__order", "-date_applied")

        if sort_by == "company":
            print('sorting by company name')
            if sort_order == "asc":
                applications = applications.order_by("company__name")
            else:
                applications = applications.order_by("-company__name")
        elif sort_by == "role":
            if sort_order == "asc":
                applications = applications.order_by("job__title")
            else:
                applications = applications.order_by("-job__title")
        elif sort_by == "salary":
            if sort_order == "asc":
                applications = applications.order_by("job__salary_max")
            else:
                applications = applications.order_by("-job__salary_max")
        elif sort_by == "applied":
            if sort_order == "asc":
                applications = applications.order_by("created")
            else:
                applications = applications.order_by("-created")
        elif sort_by == "last_email":
            if sort_order == "asc":
                applications = applications.order_by("date_of_last_email")
            else:
                applications = applications.order_by("-date_of_last_email")
        elif sort_by == "days":
            today = timezone.now().date()
            if sort_order == "asc":
                applications = applications.annotate(
                    days_since_last_email=ExpressionWrapper(
                        Value(today) - Coalesce(F('date_of_last_email'), Value(today)),
                        output_field=CustomDurationField()
                    )
                ).extra(select={'days_int': 'EXTRACT(DAY FROM "date_of_last_email")'}).order_by("days_int")
            else:
                applications = applications.annotate(
                    days_since_last_email=ExpressionWrapper(
                        Value(today) - Coalesce(F('date_of_last_email'), Value(today)),
                        output_field=CustomDurationField()
                    )
                ).extra(select={'days_int': 'EXTRACT(DAY FROM "date_of_last_email")'}).order_by("-days_int")
                
        elif sort_by == "email":
            if sort_order == "asc":
                applications = applications.annotate(email_count=Count('email')).order_by("email_count")
            else:
                applications = applications.annotate(email_count=Count('email')).order_by("-email_count")



        return (
            applications
            
        )




    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stages"] = Stage.objects.annotate(count=Count('application')).order_by("-order")

        min_max_dates = Application.objects.aggregate(Min('created'), Max('created'))

        start_date = min_max_dates['created__min']
        end_date = min_max_dates['created__max']

        if start_date and end_date:
            # Normalize start and end dates to start of day
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

            # Fetch applications count per day
            applications_by_day = Application.objects.annotate(date=TruncDay('created')).values('date').annotate(application_count=Count('pk')).order_by('date')

            # Create a dictionary from applications_by_day with date as the key
            application_dict = {entry["date"].date(): entry["application_count"] for entry in applications_by_day}

            # Generate all dates between start and end dates
            all_dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

            # Generate labels and application_counts
            labels = [date.strftime("%m/%d/%Y") for date in all_dates]
            application_counts = [application_dict.get(date.date(), 0) for date in all_dates]

            data_chart1 = {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Applications",
                        "data": application_counts,
                        "backgroundColor": "rgba(255, 99, 132, 0.2)",
                        "borderColor": "rgba(255, 99, 132, 1)",
                        "borderWidth": 1,
                    }
                ],
            }
            context["data_chart1"] = data_chart1

        sort_by = self.request.GET.get("sort_by", "applied")
        sort_order = self.request.GET.get("sort_order", "desc")
        context["sort_by"] = sort_by
        context["sort_order"] = sort_order
        context["stage"] = self.request.GET.get('stage', 'Scheduled')
        
        return context





from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.utils.decorators import method_decorator

@method_decorator(vary_on_cookie, name='dispatch')
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')  # cache for 1 day

class Index(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_companies = Company.objects.all()
        companies = list(all_companies)
        random.shuffle(companies)
        context["companies"] = companies[:50]
        context["company_count"] = all_companies.count()
        context["job_count"] = Job.objects.all().count()
        context["sources_count"] = Source.objects.all().count()
        context["sessions_count"] = Session.objects.all().count()

        time_threshold = timezone.now() - timedelta(hours=24)

        # Annotate each user with the count of their applications and applications in the last 24 hours
        users_with_counts = User.objects.annotate(
            total_applications=Count('application'),
            applications_last_24hr=Count(
                'application',
                filter=Q(application__created__gte=time_threshold)
            )
        )

        # Build list of dictionaries
        user_applications = [
            {
                'total_applications': user.total_applications,
                'applications_last_24hr': user.applications_last_24hr,
            }
            for user in users_with_counts
        ]

        # Sort by total_applications, highest to lowest
        user_applications.sort(key=lambda x: x['total_applications'], reverse=True)

        context["user_applications"] = user_applications[:3]

        return context



from django.db.models import F, Q
from django.views import generic
from django.shortcuts import get_object_or_404
from .models import Company  # Replace ".models" with your actual path to models if needed

from django.shortcuts import get_object_or_404

from requests.exceptions import RequestException

from django.http import HttpResponse
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from django.core.files.base import ContentFile
from PIL import Image
import io
import os

class CompanyDetailView(generic.DetailView):
    model = Company
    template_name = "company_detail.html"




    def get(self, request, *args, **kwargs):
        company = get_object_or_404(self.get_queryset(), slug=self.kwargs["slug"])
        self.object = company

        context = self.get_context_data(object=company)
        try:
            context["next_company"] = Company.objects.get(id=company.id + 1)
        except:
            context["next_company"] = Company.objects.all().order_by('?').first()
                
        if (
            not company.website_status_updated
            or (datetime.now(timezone.utc) - company.website_status_updated).days >= 7
        ):
            website = company.website if company.website else f"https://{company.slug}.com"

            try:
                response = requests.get(website, timeout=10)
            except RequestException as e:
                company.website_status = 500
                company.website_status_updated = timezone.now()
                company.save()

                # You may want to log the exception here or handle it in some way
                # For now, let's just ignore it and return the existing context

                return self.render_to_response(context)

            company.website_status_updated = timezone.now()

            if not company.website and company.name.lower() in response.text.lower():
                company.website = response.url
            company.website_status = response.status_code
            company.save()

        if not company.website and company.email:
            company.website = f"https://{company.email.split('@')[1]}"
            company.save()
        
            # disable screenshot code until we can get it working on render
            # if company.website:
            #     from selenium.webdriver.chrome.service import Service
            #     logger.info('getting screenshot')
            #     #service = Service(executable_path=ChromeDriverManager().install())

            #     service = Service(executable_path="/opt/render/project/.render/chrome/chromedriver")

            #     logger.info('setting options')
            #     options = webdriver.ChromeOptions()
            #     options.binary_location = "/opt/render/project/.render/chrome/opt/google/chrome/google-chrome" 
            #     options.page_load_strategy = 'eager'
            #     options.add_argument("--headless")  # Ensure GUI is off
            #     options.add_argument("--no-sandbox")
            #     options.add_argument("--disable-dev-shm-usage")
            #     options.add_argument("--window-size=1920,1080")  # Set window size to standard desktop size
            #     options.add_argument("--hide-scrollbars")  # Hide scrollbars on screenshot

            #     logger.info('getting browser')
            #     browser = webdriver.Chrome(service=service, options=options)
            #     browser.set_page_load_timeout(10) 

            #     logger.info('getting url')
            #     logger.info(company.website)

            #     url = company.website  # The URL you want to take a screenshot of
            #     try:
            #         browser.get(url)
            #         logger.info('getting screenshot')

            #         screenshot = browser.get_screenshot_as_png()

            #         file_name = f"screenshot_{company.slug}.png"
            #         company.screenshot.save(file_name, ContentFile(screenshot), save=True)

            #     except TimeoutException:
            #         logger.error(f"Timeout exceeded for URL {url}")

            #     browser.quit()

        return self.render_to_response(context)





def add_job_link(request, slug):
    company = get_object_or_404(Company, slug=slug)
    if request.method == "POST":
        job_link = request.POST.get("job_link")
        job_link = job_link.strip()
        # check that job_link contains greenhouse or lever or return error
        if "lever" not in job_link and "greenhouse" not in job_link:
            return render(
                request,
                "company_detail.html",
                {"company": company, "error": "Invalid job link"},
            )


        job = Job(link=job_link, company=company)
        job.save()
        return redirect("company_detail", slug=slug)

