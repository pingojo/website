from website.utils import get_website_title, send_slack_notification
from django.views.generic.detail import DetailView
from website.models import Application
from django.views.generic.base import TemplateView
from django.views.generic import ListView, CreateView
from django.utils import timezone
from django.utils import timezone

from django.views import generic

from django.shortcuts import get_object_or_404, redirect
from .models import Email, Job, Search
import random
from django.views import View
from django.http import JsonResponse
from .models import Company, Stage
from datetime import datetime

from django.shortcuts import render
from .models import Job

from bs4 import BeautifulSoup
import requests
from django.http import JsonResponse

from django.shortcuts import render
from .models import Job, Company
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from .models import Application

from django.core.paginator import Paginator
from django.views.generic import DetailView
from .models import Job
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Company, Role
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.views import View
from .forms import ResumeUploadForm

# from pyresparser import ResumeParser
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .parse_resume import parse_resume
import tempfile
import os
from django.utils.text import slugify
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Application, Stage
from django.utils import timezone

import requests
from django.views import View
from django.http import JsonResponse
from .models import Company
from datetime import datetime

@require_POST
def update_application_stage(request):
    application_id = request.POST.get("application_id")
    stage_id = request.POST.get("stage_id")

    try:
        application = Application.objects.get(pk=application_id)
        stage = Stage.objects.get(pk=stage_id)

        application.stage = stage
        application.save()

        messages.success(request, "Application stage updated successfully.")

    except Application.DoesNotExist:
        messages.error(request, "Application not found.")
    except Stage.DoesNotExist:
        messages.error(request, "Stage not found.")
    except Exception as e:
        messages.error(request, f"Error updating application stage: {e}")

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


from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime
from django.utils.text import slugify

class ApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        emails = Email.objects.filter(application__user=request.user).select_related('application__job__role', 'application__company')

        data = [{
            'email_id': email.gmail_id,
            'subject': email.application.job.role.title,
            'company_name': email.application.company.name,
            'company_slug': email.application.company.slug,
            'job_link': email.application.job.link,
        } for email in emails]

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
            role, _ = Role.objects.get_or_create(title=role_title)

        company, _ = Company.objects.get_or_create(slug=slugify(company_name), defaults={"name": company_name})

        max_stage = Stage.objects.all().order_by("order").last()
        max_stage = max_stage.order if max_stage else 0

        job, _ = Job.objects.update_or_create(company=company, defaults={"role": role, "slug": slugify(company)})

        stage, _ = Stage.objects.get_or_create(name=stage_name, defaults={"order": max_stage + 1})

        if stage_name == "Applied":
            try:
                original_date = datetime.strptime(email_date_str, "%a, %b %d, %Y, %I:%M %p")
            except:
                original_date = datetime.strptime(email_date_str, "%b %d, %Y, %I:%M %p")

            original_date = original_date.astimezone().replace(tzinfo=None)
            date_applied = original_date.strftime("%Y-%m-%d %H:%M:%S")

        application, created = Application.objects.get_or_create(
            user=request.user, job=job, company=company, defaults={"stage": stage, "date_applied": date_applied}
        )

        if stage_name in ["Passed", "Next", "Scheduled"]:
            original_date = datetime.strptime(email_date_str, "%a, %b %d, %Y, %I:%M %p")
            original_date = original_date.astimezone().replace(tzinfo=None)
            application.stage = stage

        if not created and application.date_applied and original_date:
            original_date = timezone.make_aware(original_date, timezone.get_current_timezone())
            if application.date_applied > original_date:
                application.date_applied = original_date

        try:
            email_date = timezone.datetime.strptime(email_date_str, "%a, %b %d, %Y, %I:%M %p")
        except:
            email_date = timezone.datetime.strptime(email_date_str, "%b %d, %Y, %I:%M %p")

        email_date_aware = timezone.make_aware(email_date, timezone.get_current_timezone())

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

        total_applications = Application.objects.filter(user=request.user).count()

        response_data = {"total_applications": total_applications}

        return JsonResponse(response_data, status=status.HTTP_201_CREATED)


class JobDetailView(DetailView):
    model = Job
    template_name = "job_detail.html"
    context_object_name = "job"


def privacy_policy(request):
    return render(request, "privacy_policy.html")


def terms_of_service(request):
    return render(request, "terms_of_service.html")


def search(request):
    search_query = request.GET.get("search", "")

    if search_query:
        jobs = Job.objects.filter(
            Q(title__icontains=search_query) | Q(company__name__icontains=search_query)
        )
        companies = Company.objects.filter(name__icontains=search_query)
    else:
        jobs = Job.objects.all()
        companies = Company.objects.all()

    search = Search(
        query=search_query,
        matched_job_count=jobs.count(),
        matched_company_count=companies.count(),
        # matched_skill_count=matched_skill_count,
        # matched_role_count=matched_role_count
    )
    search.save()

    send_slack_notification(search)

    jobs_paginator = Paginator(jobs, 10)  # Show 10 jobs per page
    jobs_page = request.GET.get("jobs_page", 1)
    paginated_jobs = jobs_paginator.get_page(jobs_page)

    companies_paginator = Paginator(companies, 10)  # Show 10 companies per page
    companies_page = request.GET.get("companies_page", 1)
    paginated_companies = companies_paginator.get_page(companies_page)

    return render(
        request,
        "search.html",
        {
            "paginated_jobs": paginated_jobs,
            "paginated_companies": paginated_companies,
            "search_query": search_query,
        },
    )


def scrape_job(request):
    url = request.GET.get("url", "")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    job_title = ""
    company_name = ""
    return JsonResponse({"job_title": job_title, "company_name": company_name})


class DashboardView(LoginRequiredMixin, ListView):
    template_name = "dashboard.html"
    context_object_name = "applications"

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user).order_by(
            "-stage__order", "-date_applied"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stages"] = Stage.objects.all().order_by("-order")
        return context


class Index(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_companies = Company.objects.all()
        companies = list(all_companies)
        random.shuffle(companies)
        context["companies"] = companies[:50]
        context["company_count"] = all_companies.count()
        return context


class CompanyDetailView(generic.DetailView):
    model = Company
    template_name = "company_detail.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Company, slug=self.kwargs["slug"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_company = self.get_object()
        prev_company = (
            Company.objects.filter(name__lt=current_company.name)
            .order_by("-name")
            .first()
        )
        next_company = (
            Company.objects.filter(name__gt=current_company.name)
            .order_by("name")
            .first()
        )
        context["prev_company"] = prev_company
        context["next_company"] = next_company
        return context


def add_job_link(request, slug):
    company = get_object_or_404(Company, slug=slug)
    if request.method == "POST":
        job_link = request.POST.get("job_link")
        job = Job(link=job_link, company=company)
        job.save()
        return redirect("company_detail", slug=slug)





class UpdateWebsiteStatusView(View):
    def get_company(self, company_id):
        try:
            return Company.objects.get(pk=company_id)
        except Company.DoesNotExist:
            return None

    def update_status(self, company, status):
        company.website_status = status
        company.website_status_updated = timezone.now()
        company.save()

    def get(self, request, *args, **kwargs):
        company_id = request.GET.get("company_id")
        company = self.get_company(company_id)
        if not company:
            return JsonResponse(
                {"status": "error", "message": "Company not found"}, status=404
            )

        if (
            not company.website_status_updated
            or (datetime.now() - company.website_status_updated).days >= 7
        ):
            response = requests.get(company.website)
            self.update_status(company, response.status_code)

        return JsonResponse(
            {"status": "success", "website_status": company.website_status}
        )

    def post(self, request, *args, **kwargs):
        company_id = request.POST.get("company_id")
        status = request.POST.get("status")

        company = self.get_company(company_id)
        if not company:
            return JsonResponse(
                {"status": "error", "message": "Company not found"}, status=404
            )

        self.update_status(company, int(status))
        return JsonResponse({"status": "success"})
