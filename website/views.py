import os
import tempfile
from datetime import datetime, timedelta

import html2text
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Count, ExpressionWrapper, F, Max, Min, Q, Value
from django.db.models.functions import Coalesce, TruncDay
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views import View, generic
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, ListView
from requests.exceptions import RequestException
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from website.models import Application, Company, Email, Job, Role, Stage
from website.utils import get_website_title

from .forms import (
    CompanyUpdateForm,
    EditAccountForm,
    JobForm,
    LinkForm,
    ProfileForm,
    PromptForm,
    ResumeUploadForm,
)
from .models import BouncedEmail, Link, Profile, Prompt, Search, Skill, Source
from .parse_resume import parse_resume


class GetCompanyEmailView(View):
    def get(self, request):
        company_name = request.GET.get("company_name")
        company = Company.objects.filter(name=company_name).first()
        if company:
            return JsonResponse({"email": company.email})

        return JsonResponse({"error": "Company not found"}, status=404)


class ProfileListView(ListView):
    model = Profile
    context_object_name = "profiles"

    def get_queryset(self):
        return Profile.objects.filter(is_public=True).order_by("-web_views")


class BouncedEmailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Extract email and reason from the request
        email = request.data.get("email")
        reason = request.data.get("reason")

        if not email:
            raise ValidationError({"email": "This field is required."})
        if not reason:
            raise ValidationError({"reason": "This field is required."})

        # Check for an active application to the company with the given email
        application = Application.objects.filter(
            company__email=email,
            user=request.user,
        ).first()

        if not application:
            return JsonResponse(
                {"detail": "No active application found for this company."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create a BouncedEmail entry
        bounced_email, created = BouncedEmail.objects.get_or_create(
            company=application.company, email=email, defaults={"reason": reason}
        )

        if not created:
            return JsonResponse(
                {"detail": "Bounced email entry already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        # Clear the email field on the Company model
        company = application.company
        company.email = ""
        company.save()

        return JsonResponse(
            {
                "detail": "Bounced email processed successfully. You can delete this full thread."
            },
            status=status.HTTP_201_CREATED,
        )


@login_required
def application_count(request):
    # Get the current time
    now = timezone.now()
    # Calculate the time 24 hours ago
    start_time = now - timezone.timedelta(days=1)
    # Filter applications created in the past 24 hours
    count = Application.objects.filter(
        user=request.user, created__gte=start_time
    ).count()
    return JsonResponse({"count": count})


@login_required
def delete_link(request, link_id):
    if request.method == "GET":
        link = get_object_or_404(Link, id=link_id)
        profile = request.user.profile
        profile.links.remove(link)
        links = profile.links.all()
        return HttpResponse(
            render_to_string(
                "partials/_links_list.html", {"links": links}, request=request
            )
        )


@login_required
def delete_role(request, role_id):
    if request.method == "GET":
        role = get_object_or_404(Role, id=role_id)
        profile = request.user.profile
        profile.roles.remove(role)
        roles = profile.roles.all()
        return HttpResponse(
            render_to_string(
                "partials/_roles_list.html", {"roles": roles}, request=request
            )
        )


@login_required
@require_http_methods(["POST"])
def update_roles(request):
    user_profile = request.user.profile
    role_id = request.POST.get("role_id")
    role = Role.objects.get(id=role_id)
    if role not in user_profile.roles.all():
        user_profile.roles.add(role)
        user_profile.save()

    roles = user_profile.roles.all()
    html = render_to_string(
        "partials/_roles_list.html", {"roles": roles}, request=request
    )
    return HttpResponse(html)


def role_search(request):
    query = request.GET.get("role", "")
    roles = Role.objects.filter(title__icontains=query)[:10]
    return render(request, "partials/role_suggestions.html", {"roles": roles})


@login_required
def delete_skill(request, skill_id):
    if request.method == "GET":
        skill = get_object_or_404(Skill, id=skill_id)
        profile = request.user.profile
        profile.skills.remove(skill)
        skills = profile.skills.all()
        return HttpResponse(
            render_to_string(
                "partials/_skills_list.html", {"skills": skills}, request=request
            )
        )


@login_required
@require_http_methods(["POST"])
def update_skills(request):
    user_profile = request.user.profile
    skill_id = request.POST.get("skill_id")
    skill = Skill.objects.get(id=skill_id)
    if skill not in user_profile.skills.all():
        user_profile.skills.add(skill)
        user_profile.save()

    skills = user_profile.skills.all()
    html = render_to_string(
        "partials/_skills_list.html", {"skills": skills}, request=request
    )
    return HttpResponse(html)


def skill_search(request):
    query = request.GET.get(
        "skill", ""
    )  # This should match the name of the query parameter sent by HTMX
    skills = Skill.objects.filter(name__icontains=query)[:10]
    return render(request, "partials/skill_suggestions.html", {"skills": skills})


from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import get_object_or_404, render


def profile(request, username=None):
    if username:
        # Fetch the user or return a 404 immediately if not found
        user = get_object_or_404(User, username=username)
        # increment user.profile.views_count
        user.profile.web_views += 1
        user.profile.save()

        # If the user is found but their profile is not public, return a 404
        if not user.profile.is_public:
            raise Http404

        # If the user's profile is public, render the public profile page
        return render(
            request,
            "account/public_profile.html",
            {
                "skills": user.profile.skills.all(),
                "roles": user.profile.roles.all(),
                "user": user,
                "links": user.profile.links.all(),
            },
        )

    # If no username is provided, return a 404 as well
    raise Http404


@login_required
def profile_view(request, prompt_id=None):
    # create Profile for the user if it doesn not exist
    Profile.objects.get_or_create(user=request.user)
    prompt = None
    if prompt_id:
        prompt = Prompt.objects.get(id=prompt_id)

    if request.method == "POST":
        if "account_form" in request.POST:
            account_form = EditAccountForm(request.POST, instance=request.user)
            if account_form.is_valid():
                account_form.save()
                messages.success(request, "Your profile has been updated.")
                return redirect("profile")
            prompt_form = PromptForm(instance=prompt)
        elif "prompt_form" in request.POST:
            prompt_form = PromptForm(request.POST, instance=prompt)
            if prompt_form.is_valid():
                prompt = prompt_form.save(commit=False)
                prompt.user = request.user
                prompt.save()
                messages.success(request, "Your prompt has been updated.")
                return redirect("profile")
            account_form = EditAccountForm(instance=request.user)
        if "profile_form" in request.POST:  # This handles the profile form
            profile_form = ProfileForm(request.POST, instance=request.user.profile)
            if profile_form.is_valid():
                profile_form.save()

                messages.success(request, "Your profile settings have been updated.")
                return redirect("profile")
            else:
                account_form = EditAccountForm(instance=request.user)
                messages.error(request, "Please correct the error below.")
        if "add_link" in request.POST:
            links_form = LinkForm(request.POST)

            link_url = request.POST.get("url")

            link_url = link_url.replace("https://", "")
            link_url = link_url.replace("http://", "")
            link_url = link_url.replace("www.", "")

            link_title = get_website_title(link_url)

            link, _ = Link.objects.get_or_create(url=link_url, title=link_title)

            if link not in request.user.profile.links.all():
                request.user.profile.links.add(link)
                request.user.profile.save()

                messages.success(request, "You added a link")
                return redirect("profile")
            else:
                account_form = LinkForm(instance=request.user)
                messages.error(request, "Please correct the error below.")
    else:
        account_form = EditAccountForm(instance=request.user)
        prompt_form = PromptForm(instance=prompt)
        # bio_form = BioForm(instance=request.user.profile)
        profile_form = ProfileForm(instance=request.user.profile)
        links_form = LinkForm()

    prompts = Prompt.objects.filter(user=request.user)
    skills = request.user.profile.skills.all()
    roles = request.user.profile.roles.all()
    links = request.user.profile.links.all()

    context = {
        "account_form": account_form,
        "prompt_form": prompt_form,
        "prompts": prompts,
        "skills": skills,
        "profile_form": profile_form,
        "roles": roles,
        "links": links,
        "links_form": links_form,
    }
    return render(request, "account/profile.html", context)


def is_authenticated(request):
    if request.user.is_authenticated:
        return JsonResponse({"is_authenticated": True})
    else:
        return JsonResponse({"is_authenticated": False})


class CustomDurationField(models.DurationField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        return timezone.timedelta(seconds=value.total_seconds()).days


import logging
import re

from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Company, Job, Role

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


# reqired login


@login_required
def update_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == "POST":
        # job.title = request.POST.get('title')
        # job.description = request.POST.get('description')
        if not job.role:
            role = request.POST.get("role")
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
                        "icon_emoji": ":tada:",
                    }
                    requests.post(webhook_url, json=payload)
                return HttpResponse(role)

    return JsonResponse({"success": False})


@login_required
def update_company(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    if request.method == "POST":
        email = request.POST.get("email")
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return JsonResponse({"success": False, "error": "Invalid email address"})

        if not company.email:
            company.email = email or company.email

        if not company.twitter_url:
            company.twitter_url = request.POST.get("twitter_url") or company.twitter_url

        if not company.number_of_employees_min:
            company.number_of_employees_min = (
                request.POST.get("number_of_employees_min")
                or company.number_of_employees_min
            )

        if not company.number_of_employees_max:
            company.number_of_employees_max = (
                request.POST.get("number_of_employees_max")
                or company.number_of_employees_max
            )

        if not company.description:
            company.description = request.POST.get("description") or company.description

        if not company.website:
            company.website = request.POST.get("website") or company.website

        if not company.city:
            company.city = request.POST.get("city") or company.city

        if not company.state:
            company.state = request.POST.get("state") or company.state

        if not company.country:
            company.country = request.POST.get("country") or company.country

        if not company.ceo:
            company.ceo = request.POST.get("ceo") or company.ceo

        if not company.ceo_twitter:
            company.ceo_twitter = request.POST.get("ceo_twitter") or company.ceo_twitter

        company.save()

        webhook_url = settings.SLACK_WEBHOOK_URL

        if webhook_url:
            message = f"{company.name} updated:" + str(request.POST)
            payload = {
                "text": message,
                "channel": "#updates",
                "username": "Company Update",
                "icon_emoji": ":tada:",
            }
            requests.post(webhook_url, json=payload)

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request"})


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
        application = get_object_or_404(
            Application, pk=request.POST.get("application_id", None)
        )

        new_email = request.POST.get("email", None)
        if new_email:
            regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            if not re.match(regex, new_email):
                return JsonResponse({"error": "Invalid email address"}, status=400)

            if application.user == request.user and new_email:
                application.job.company.email = new_email
                application.job.company.save()
                application.job.company.refresh_from_db()
                return render(
                    request,
                    "partials/email.html",
                    {
                        "application": application,
                    },
                )
        new_role = request.POST.get("role", None)

        if new_role:
            role_slug = slugify(new_role[:50])
            role, _ = Role.objects.get_or_create(
                slug=role_slug, defaults={"title": new_role}
            )
            application.job.role = role
            application.job.save()
            return HttpResponse(new_role)

    return JsonResponse({"error": "Invalid Method or Missing email field"}, status=400)


from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Case, IntegerField, Q, Value, When


class JobListView(ListView):
    model = Job
    context_object_name = "jobs"
    paginate_by = 50
    queryset = None
    server_time = timezone.now()
    server_timestamp = int(server_time.timestamp() * 1000)

    def dispatch(self, *args, **kwargs):
        job_count = settings.JOB_COUNT
        session_key = self.request.session.session_key or "anonymous"

        query_params = self.request.GET.urlencode()
        user_specific_cache_key = (
            f"{settings.JOB_LIST_CACHE_KEY}_{session_key}_{job_count}_{query_params}"
        )

        response = cache.get(user_specific_cache_key)

        if not response:
            # Generate the response
            response = super(JobListView, self).dispatch(*args, **kwargs)
            if hasattr(response, "render") and callable(response.render):
                response.add_post_render_callback(
                    lambda r: cache.set(user_specific_cache_key, r, 60 * 60)
                )
            else:
                cache.set(user_specific_cache_key, response, 60 * 60)
        return response

    def get_queryset(self):
        if not self.queryset:
            search_query = re.sub(
                r"[^a-zA-Z0-9,. ]", "", self.request.GET.get("search", "").strip()
            )

            if search_query:
                query = SearchQuery(search_query)
                queryset = (
                    Job.objects.select_related("company", "role")
                    .annotate(rank=SearchRank(F("search_vector"), query))
                    .filter(rank__gt=0)
                    .order_by("-rank")
                )

                if queryset.exists():
                    self.queryset = queryset
                    job_count = self.queryset.count()
                    search = Search(query=search_query, matched_job_count=job_count)
                    search.save()
                    # send_slack_notification(search)
                else:
                    self.queryset = Job.objects.select_related("company", "role").all()
            else:
                self.queryset = Job.objects.select_related("company", "role").order_by(
                    F("posted_date").desc(nulls_last=True)
                )

            if self.request.GET.get("apply_by_email", ""):
                self.queryset = self.queryset.filter(
                    company__email__isnull=False
                ).exclude(company__email__exact="")

            if self.request.GET.get("view") == "grid":
                self.template_name = "website/job_grid.html"

            if self.request.user.is_authenticated:
                # Exclude jobs the user has applied for
                applied_jobs = Application.objects.filter(
                    user=self.request.user
                ).values_list("job_id", flat=True)
                queryset = self.queryset.exclude(id__in=applied_jobs)

            ordering = self.request.GET.get("ordering")
            if ordering and ordering.lstrip("-") in [
                "created",
                "posted_date",
                "salary_min",
                "salary_max",
                "title",
                "location",
                "job_type",
            ]:
                self.queryset = self.queryset.order_by(ordering)

        return self.queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_jobs = self.object_list.count()  # Use count() on the object list
        context["total_jobs"] = total_jobs
        context["server_timestamp"] = self.server_timestamp
        context["sessions_count"] = Session.objects.all().count()
        if self.request.user.is_authenticated:
            if self.request.user.prompt_set.all():
                context["prompt"] = Prompt.objects.filter(
                    user=self.request.user
                ).first()
                context["stages"] = Stage.objects.annotate(
                    count=Count(
                        "application", filter=Q(application__user=self.request.user)
                    )
                ).order_by("-order")

        return context


class SourceListView(ListView):
    model = Source
    template_name = "sources.html"
    context_object_name = "sources"

    def get_queryset(self):
        queryset = super().get_queryset()
        sort = self.request.GET.get("sort", "job_count")
        direction = self.request.GET.get("direction", "desc")
        if sort:
            if direction == "desc":
                sort = "-" + sort
            queryset = queryset.order_by(sort)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_sort"] = self.request.GET.get("sort", "")
        context["current_direction"] = self.request.GET.get("direction", "")
        return context


class CompanyListView(ListView):
    model = Company
    template_name = "company_list.html"
    context_object_name = "companies"
    paginate_by = 100

    def get_queryset(self):
        order = self.request.GET.get("order")

        companies = cache.get("companies_queryset")
        if not companies:
            companies = Company.objects.prefetch_related("application_set")
            cache.set("companies_queryset", companies, 60 * 60)  # Cache for 1 hour

        if order:
            companies = companies.order_by(order)

        return companies

    def post(self, request, *args, **kwargs):
        company_id = request.POST.get("company_id")
        company = get_object_or_404(Company, id=company_id)
        form = CompanyUpdateForm(request.POST, instance=company)

        if form.is_valid():
            form.save()

        order = request.POST.get("order")
        page = request.POST.get("page")

        redirect_url = reverse("company_list") + "?"
        if order:
            redirect_url += f"order={order}&"
        if page:
            redirect_url += f"page={page}"

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
            return JsonResponse(
                {
                    "status": "error",
                    "message": "You are not authorized to delete this application.",
                }
            )


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
            return render(
                request,
                "partials/link.html",
                {"application": application, "status": "success"},
            )
        else:
            # Return an HTML snippet of the error message, styled red
            return render(
                request,
                "partials/link.html",
                {
                    "application": application,
                    "status": "error",
                    "message": "You are not authorized to update this application.",
                },
            )


def update_application_stage(request):
    if request.method == "POST":
        application_id = request.POST.get("application_id")
        stage_id = request.POST.get("stage_id")
    elif request.method == "GET":
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
        return JsonResponse(
            {"success": False, "message": list(messages.get_messages(request))},
            status=400,
        )
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

        company_name = data.get("company", "").strip()
        role_title = data.get("title", "").strip()

        posted_date = data.get("datePosted")
        salaryRange = data.get("salaryRange", " ").strip()
        CompanySalary = data.get("companySalary", " ").strip()
        if not salaryRange and CompanySalary:
            salaryRange = CompanySalary
        location = data.get("location", " ").strip()
        website = data.get("website", " ").strip()
        country = data.get("companyAddress", " ").strip()
        if country and not location:
            location = country
        job_type = data.get("companyStatus", " ").strip()
        remote = data.get("companyRemote", " ").strip() == "Yes" or True
        CompanyPhone = data.get("companyPhone", " ").strip()
        CompanyEmail = data.get("companyEmail", " ").strip()
        description = data.get("description", " ").strip()

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
            },
        )

        if description:
            converter = html2text.HTML2Text()
            converter.ignore_links = False

            if "&lt;" in description:
                soup = BeautifulSoup(description, "html.parser")
                description = soup.get_text()

            markdown = converter.handle(description)
            description = markdown

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

        settings.JOB_COUNT = Job.objects.count()

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
            {
                "applications": application_data,
                "job_url": "https://"
                + Site.objects.get_current().domain
                + "/job/"
                + job.slug,
            },
            status=status.HTTP_200_OK,
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

        now = timezone.now()
        # Calculate the time 24 hours ago
        start_time = now - timezone.timedelta(days=1)
        # Filter applications created in the past 24 hours
        today_count = Application.objects.filter(
            user=request.user, created__gte=start_time
        ).count()

        data = {
            "emails": email_data,
            "counts": stage_counts_dict,
            "today_count": today_count,
        }

        return Response(data)

    def post(self, request):
        data = request.data
        company_name = data.get("company_name")
        role_title = data.get("role_title", "").strip()
        email_date_str = data.get("email_date")
        stage_name = data.get("stage_name")
        to_email = data.get("to_email", "").strip()
        gmail_id = data.get("gmail_id")

        role, company, max_stage, job, stage, date_applied, original_date = (None,) * 7

        if role_title:
            role_slug = slugify(role_title[:50])
            role, _ = Role.objects.get_or_create(
                slug=role_slug, defaults={"title": role_title}
            )

        company, _ = Company.objects.get_or_create(
            slug=slugify(company_name),
            defaults={"name": company_name, "email": to_email},
        )
        if to_email and company.email != to_email:
            company.email = to_email
            company.save()

        max_stage = Stage.objects.all().order_by("order").last()
        max_stage = max_stage.order if max_stage else 0

        job, _ = Job.objects.update_or_create(
            company=company, role=role, slug=slugify(role.title + "-at-" + company.name)
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
            Email.objects.get_or_create(
                gmail_id=gmail_id,
                defaults={
                    "date": email_date,
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
            "company_name": company_name,
            "company_slug": company.slug,
            "job_link": job.link,
            "job_role": role.title if role else None,
            "stage": stage.name,
        }

        now = timezone.localtime()  # Ensure you're using the user's local timezone
        start_time = datetime.combine(now.date(), datetime.min.time())
        today_count = Application.objects.filter(
            user=request.user, created__gte=start_time
        ).count()

        data = {"email": email_data, "counts": stage_counts, "today_count": today_count}

        return JsonResponse(data, status=status.HTTP_201_CREATED)


from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from .models import Application, Job


class JobDetailView(DetailView):
    model = Job
    template_name = "job_detail.html"
    context_object_name = "job"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.get_object()

        # Generate cache key based on job id and user id
        cache_key = f'job_detail_{job.id}_user_{self.request.user.id if self.request.user.is_authenticated else "anonymous"}'
        context_data = cache.get(cache_key)

        if not context_data:
            context_data = {}
            if self.request.user.is_authenticated:
                applications = Application.objects.filter(
                    job=job, user=self.request.user
                )
                context_data["applications"] = applications
            context_data["stages"] = Stage.objects.annotate(
                count=Count("application")
            ).order_by("-order")

            cache.set(cache_key, context_data, 60 * 60 * 24 * 30)

        context.update(context_data)
        return context


def privacy_policy(request):
    return render(request, "privacy_policy.html")


def terms_of_service(request):
    return render(request, "terms_of_service.html")


def scrape_job(request):
    url = request.GET.get("url", "")

    if not "greenhouse" in url and not "lever" in url:
        return JsonResponse({"job_title": "", "company_name": ""})

    job_title = ""
    company_name = ""
    return JsonResponse({"job_title": job_title, "company_name": company_name})


class DashboardView(LoginRequiredMixin, ListView):
    template_name = "dashboard.html"
    context_object_name = "applications"
    paginate_by = 50

    def get_queryset(self):
        stage = self.request.GET.get("stage", "Scheduled")
        stage_obj = get_object_or_404(Stage, name=stage)

        sort_by = self.request.GET.get("sort_by", "last_email")
        if "-" in sort_by:
            sort_by = sort_by[1:]
            sort_order = "desc"
        else:
            sort_order = self.request.GET.get("sort_order", "asc")

        order_prefix = "" if sort_order == "asc" else "-"

        sort_fields = {
            "company": "company__name",
            "role": "job__title",
            "salary_max": "job__salary_max",
            "salary_min": "job__salary_min",
            "applied": "created",
            "last_email": "date_of_last_email",
        }

        applications = (
            Application.objects.filter(user=self.request.user, stage=stage_obj)
            .prefetch_related(
                "company", "stage", "job", "job__company", "job__role", "email_set"
            )
            .order_by("-stage__order", "-date_applied")
        )

        if sort_by in sort_fields:
            applications = applications.order_by(
                f"{order_prefix}{sort_fields[sort_by]}"
            )
        elif sort_by == "days":
            today = timezone.now().date()
            applications = (
                applications.annotate(
                    days_since_last_email=ExpressionWrapper(
                        Value(today) - Coalesce(F("date_of_last_email"), Value(today)),
                        output_field=CustomDurationField(),
                    )
                )
                .extra(select={"days_int": 'EXTRACT(DAY FROM "date_of_last_email")'})
                .order_by(f"{order_prefix}days_int")
            )
        elif sort_by == "email":
            applications = applications.annotate(email_count=Count("email")).order_by(
                f"{order_prefix}email_count"
            )

        return applications

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stages"] = Stage.objects.annotate(
            count=Count("application", filter=Q(application__user=self.request.user))
        ).order_by("-order")
        total_jobs = Job.objects.count()  # Use count() on the object list
        context["total_jobs"] = total_jobs
        min_max_dates = Application.objects.filter(user=self.request.user).aggregate(
            Min("created"), Max("created")
        )

        start_date = min_max_dates["created__min"]
        end_date = min_max_dates["created__max"]

        if start_date and end_date:
            # Normalize start and end dates to start of day
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

            # Fetch applications count per day
            applications_by_day = (
                Application.objects.all()
                .filter(user=self.request.user)
                .annotate(date=TruncDay("created"))
                .values("date")
                .annotate(application_count=Count("pk"))
                .order_by("date")
            )

            # Create a dictionary from applications_by_day with date as the key
            application_dict = {
                entry["date"].date(): entry["application_count"]
                for entry in applications_by_day
            }

            # Generate all dates between start and end dates
            all_dates = [
                start_date + timedelta(days=i)
                for i in range((end_date - start_date).days + 1)
            ]

            # Generate labels and application_counts
            labels = [date.strftime("%m/%d/%Y") for date in all_dates]
            application_counts = [
                application_dict.get(date.date(), 0) for date in all_dates
            ]

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
        context["stage"] = self.request.GET.get("stage", "Scheduled")

        return context


# @method_decorator(vary_on_cookie, name='dispatch')
# @method_decorator(cache_page(60 * 60 * 24), name='dispatch')  # cache for 1 day
# class Index(TemplateView):
#     template_name = "index.html"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         all_companies = Company.objects.all()
#         #companies = list(all_companies)
#         #random.shuffle(companies)
#         #context["companies"] = companies[:50]
#         context["company_count"] = all_companies.count()
#         context["job_count"] = Job.objects.all().count()
#         context["sources_count"] = Source.objects.all().count()
#         context["sessions_count"] = Session.objects.all().count()

#         time_threshold = timezone.now() - timedelta(hours=24)

#         # Annotate each user with the count of their applications and applications in the last 24 hours
#         users_with_counts = User.objects.annotate(
#             total_applications=Count('application'),
#             applications_last_24hr=Count(
#                 'application',
#                 filter=Q(application__created__gte=time_threshold)
#             )
#         )

#         # # Build list of dictionaries
#         # user_applications = [
#         #     {
#         #         'total_applications': user.total_applications,
#         #         'applications_last_24hr': user.applications_last_24hr,
#         #     }
#         #     for user in users_with_counts
#         # ]

#         # # Sort by total_applications, highest to lowest
#         # user_applications.sort(key=lambda x: x['total_applications'], reverse=True)

#         # context["user_applications"] = user_applications[:3]

#         return context


from .models import Company


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
            context["next_company"] = Company.objects.all().order_by("?").first()

        if (
            not company.website_status_updated
            or (datetime.now(timezone.utc) - company.website_status_updated).days >= 7
        ):
            website = (
                company.website if company.website else f"https://{company.slug}.com"
            )

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
        return self.render_to_response(context)

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


def add_job_link(request, slug):
    if request.method == "POST":
        company = get_object_or_404(Company, slug=slug)
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


from urllib.parse import urlparse


def normalize_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc or parsed_url.path
    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def update_company_email(request):
    email = request.GET.get("email")
    if email:
        domain = email.split("@")[-1].lower()
        try:
            companies = Company.objects.filter(website__icontains=domain)
            if not companies.exists():
                messages.error(request, "No company found with the specified domain.")
                return redirect("company_list")

            matched_company = None
            for company in companies:
                company_domain = normalize_domain(company.website).lower()
                if domain == company_domain:
                    matched_company = company
                    break

            if matched_company:
                if not matched_company.email:
                    matched_company.email = email
                    matched_company.save()
                    messages.success(request, "The email address has been updated.")
                else:
                    messages.info(request, "The email address already exists.")
                return redirect("company_detail", slug=matched_company.slug)
            else:
                company_list = ", ".join([company.name for company in companies])
                messages.error(
                    request,
                    "Multiple companies found with the specified domain, they were: "
                    + company_list,
                )
                return redirect("company_list")
        except Company.DoesNotExist:
            messages.error(request, "No company found with the specified domain.")
            return redirect(
                "company_list"
            )  # Redirect to a list of companies or a suitable page

    else:
        messages.error(request, "No email address provided.")
        return redirect("company_list")
