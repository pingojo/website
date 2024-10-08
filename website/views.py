import os
import re
import tempfile
from datetime import datetime, time, timedelta
from datetime import timezone as dt_timezone

import html2text
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import models
from django.db.models import (
    Count,
    DurationField,
    ExpressionWrapper,
    F,
    IntegerField,
    Max,
    Min,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce, ExtractDay, TruncDay
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.timezone import is_naive, make_aware
from django.views import View, generic
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import DetailView, ListView
from requests.exceptions import RequestException
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
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
from .models import (
    Application,
    BouncedEmail,
    Company,
    Job,
    Link,
    Profile,
    Prompt,
    RequestLog,
    Role,
    Search,
    Skill,
    Source,
    User,
)
from .parse_resume import parse_resume


def donate(request):
    return render(request, "donate.html")
def pricing(request):
    return render(request, "pricing.html")

def job_detail_htmx(request, slug):
    job_object = get_object_or_404(Job, slug=slug)
    if request.POST.get("skill") and request.user.is_authenticated:
        skill = request.POST.get("skill")
        skill, _ = Skill.objects.get_or_create(name=skill)

        skill_name_lower = skill.name.lower()  # Convert skill name to lowercase
        jobs = Job.objects.prefetch_related('skills').all()
        matching_jobs = jobs.filter(
            description_markdown__icontains=f" {skill_name_lower}"
        )

        # Add the skill to each matching job
        for job in matching_jobs:
            if not job.skills.filter(id=skill.id).exists():  # Check if the skill is already added
                job.skills.add(skill)

        # if " " + skill.name.lower() in job.description_markdown.lower():
        #     job.skills.add(skill)
        #     job.save()
    if request.user.is_authenticated:
        applications = Application.objects.filter(
            user=request.user, job=job_object
        )
        stages = Stage.objects.all().order_by("-order")
    else:
        applications = None
        stages = None
    return render(request, "partials/job_detail_include.html", {"job": job_object, "applications": applications, "stages": stages})

@login_required
def view_resume_clicks(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    user_applications = Application.objects.filter(user=request.user, company=company)
    
    if not user_applications.exists():
        return redirect('dashboard') 
    
    resume_clicks = RequestLog.objects.filter(company=company).order_by('-created')

    context = {
        'company': company,
        'resume_clicks': resume_clicks,
    }
    
    return render(request, 'resume_clicks.html', context)

@login_required
def edit_note_view(request, application_id):
    application = get_object_or_404(Application, id=application_id, user=request.user)
    if request.method == "POST":
        note = request.POST.get("note")
        application.notes = note
        application.save()
        return JsonResponse({'status': 'success', 'note': application.notes})

    return render(request, 'partials/note_form.html', {'application': application})

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
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    def post(self, request, *args, **kwargs):
        data = request.data

        email = data.get("email", "").strip()
        reason = data.get("reason", "").strip()

        if not email:
            raise ValidationError({"email": "This field is required."})
        if not reason:
            raise ValidationError({"reason": "This field is required."})

        # if "bounce" not in reason.lower():
        #     raise ValidationError({"reason": "Invalid reason."})

        # Check if email is valid
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValidationError({"email": "Invalid email address."})

        # Check for an active application to the company with the given email
        application = Application.objects.filter(
            company__email=email,
            user=request.user,
        ).first()

        if not application:
            return Response(
                {"detail": "No active application found for this company."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create a BouncedEmail entry
        bounced_email, created = BouncedEmail.objects.get_or_create(
            company=application.company, email=email, defaults={"reason": reason}
        )

        if not created:
            return Response(
                {"detail": "Bounced email entry already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        # Clear the email field on the Company model
        company = application.company
        company.email = ""
        company.save()
        # clear the detail_ cache key
        cache_key = f'detail_{company.id}_user_{request.user.id}'
        cache.delete(cache_key)

        return Response(
            {"detail": "Bounced email processed successfully."},
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

        if email:
            company.email = email

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
        cache_key = f'detail_{company_id}_user_{request.user.id}'
        cache.delete(cache_key)

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


@login_required
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
                if new_email and re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
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
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse


class JobListView(ListView):
    model = Job
    context_object_name = "jobs"
    paginate_by = 50
    queryset = None
    from django.utils import timezone  # Ensure this is imported
    server_time = timezone.now()  # Django's timezone handling
    server_timestamp = int(server_time.timestamp() * 1000)

    def dispatch(self, *args, **kwargs):
        job_count = settings.JOB_COUNT
        session_key = self.request.session.session_key or "anonymous"
        
        # Cache key includes session and job count
        query_params = self.request.GET.urlencode()
        user_specific_cache_key = (
            f"{settings.JOB_LIST_CACHE_KEY}_{session_key}_{job_count}_{query_params}"
        )

        response = cache.get(user_specific_cache_key)
        
        if not response:
            # Generate the response if not cached
            response = super(JobListView, self).dispatch(*args, **kwargs)
            if hasattr(response, "render") and callable(response.render):
                response.add_post_render_callback(
                    lambda r: cache.set(user_specific_cache_key, r, 60 * 60)
                )
            else:
                cache.set(user_specific_cache_key, response, 60 * 60)
        
        return response

    def get_queryset(self):
        if self.queryset is None:  # Avoid re-executing the queryset
            search_type = self.request.GET.get("search_type", "").strip()
            search_query = re.sub(
                r"[^a-zA-Z0-9,.@ ]", "", self.request.GET.get("search", "").strip()
            )

            # Filters based on search type
            if search_type == "skill":
                self.queryset = Job.objects.filter(
                    skills__name__icontains=search_query
                ).select_related("company", "role").distinct()

            elif search_type == "company" and search_query:
                self.queryset = Job.objects.filter(
                    company__name__icontains=search_query
                ).select_related("company", "role").distinct()

            elif search_type == "role" and search_query:
                self.queryset = Job.objects.filter(
                    role__title__icontains=search_query
                ).select_related("company", "role").distinct()

            elif search_type == "job" and search_query:
                self.queryset = Job.objects.filter(
                    description_markdown__icontains=search_query
                ).select_related("company", "role").distinct()

            elif search_type == "email" and search_query:
                self.queryset = Job.objects.filter(
                    company__email__icontains=search_query
                ).select_related("company", "role").distinct()

            elif search_query:
                query = SearchQuery(search_query)
                queryset = Job.objects.select_related("company", "role") \
                    .annotate(rank=SearchRank(F("search_vector"), query)) \
                    .filter(rank__gt=0) \
                    .order_by("-rank")
                
                if queryset.exists():
                    self.queryset = queryset
                    job_count = self.queryset.count()
                    search = Search(query=search_query, matched_job_count=job_count)
                    search.save()
                else:
                    self.queryset = Job.objects.select_related("company", "role").all()

            else:
                self.queryset = Job.objects.select_related("company", "role") \
                    .order_by(F("posted_date").desc(nulls_last=True))

            # Filter by email if apply_by_email is set
            if self.request.GET.get("apply_by_email", ""):
                self.queryset = self.queryset.filter(
                    company__email__isnull=False
                ).exclude(company__email__exact="")

            # Change template if view is grid
            if self.request.GET.get("view") == "grid":
                self.template_name = "website/job_grid.html"

            # Apply ordering
            ordering = self.request.GET.get("ordering")
            if ordering and ordering.lstrip("-") in [
                "created", "posted_date", "salary_min", "salary_max",
                "title", "location", "job_type"
            ]:
                self.queryset = self.queryset.order_by(ordering)

        return self.queryset

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()

        # Check if all jobs belong to the same company
        company_count = self.object_list.values_list('company', flat=True).distinct().count()
        if company_count == 1:
            # Redirect to company detail page if only one company is found
            single_company = self.object_list.first().company
            return HttpResponseRedirect(reverse('company_detail', args=[single_company.slug]))

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_jobs = self.object_list.count()  # Use count() on the object list
        context["total_jobs"] = total_jobs
        context["server_timestamp"] = self.server_timestamp
        context["sessions_count"] = Session.objects.all().count()

        if self.request.user.is_authenticated:
            if self.request.user.prompt_set.exists():
                context["prompt"] = self.request.user.prompt_set.first()
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
            job.location = form.cleaned_data["city"] + ", " + form.cleaned_data["state"]
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


@login_required
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

        job_id = application.job.id
        user_id = request.user.id
        cache_key = f'detail_{job_id}_user_{user_id}'
        cache.delete(cache_key)

        # Recreate and cache the context data
        context_data = {}
        applications = Application.objects.filter(job=application.job, user=request.user)
        context_data["applications"] = applications
        context_data["stages"] = Stage.objects.annotate(
            count=Count("application")
        ).order_by("-order")

        # Set the new cache
        cache.set(cache_key, context_data, 60 * 60 * 24 * 30)  # Cache for 30 days

        

        if request.headers.get("HX-Request"):
            return JsonResponse({"status": "success", "application_id": application_id})
        else:
            messages.success(request, "Application stage updated successfully.")

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
        link_is_410 = data.get("link_is_410", False)
        if link_is_410:
            link = data.get("link")
            link_parts = link.split("/")
            job_slug = link_parts[-1]
            job = Job.objects.filter(link__contains=job_slug).first()
            if job:
                job.link_status_code = 410
                job.link_status_code_updated = timezone.now()
                job.save()
                try:
                    application = Application.objects.get(job=job, user=request.user)
                    application.stage = Stage.objects.get(name="Passed")
                    application.notes = "Link is 410"
                    application.save()
                except Application.DoesNotExist:
                    pass
                company = job.company

        else:

            company_name = data.get("company", "").strip()
            if not company_name:
                return JsonResponse(
                    {"error": "Company name is required."}, status=400
                )
            role_title = data.get("title", "").strip()

            posted_date = data.get("datePosted")
            salaryRange = data.get("salaryRange", " ").strip()
            CompanySalary = data.get("companySalary", " ").strip()
            if not salaryRange and CompanySalary:
                salaryRange = CompanySalary

            if data.get("location") is not None:
                location = data.get("location", " ").strip()
            else:
                location = " "
            website = data.get("website", "").strip()
            country = data.get("companyAddress", " ").strip()
            if country and not location:
                location = country
            job_type = data.get("companyStatus", " ").strip()
            remote = data.get("companyRemote", " ").strip() == "Yes" or True
            CompanyPhone = data.get("companyPhone", " ").strip()
            CompanyEmail = data.get("companyEmail", "").strip()
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
            company_defaults = {
                "name": company_name,
                "country": country,
                "phone": CompanyPhone,
            }

            # Only add the email if it's provided
            if CompanyEmail:
                company_defaults["email"] = CompanyEmail

            # Only add the website if it's provided
            if website:
                company_defaults["website"] = website

            # Update or create the company using the defaults
            company, _ = Company.objects.update_or_create(
                slug=slugify(company_name).strip()[:50],
                defaults=company_defaults,
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
                defaults={
                    'slug': slugify(role.title + "-at-" + company.name),
                    "posted_date": posted_date,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "link": link,
                    "title": role.title,
                    "location": location[:254],
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

        data = {
            "emails": email_data,
            "counts": stage_counts_dict,
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
        if to_email != "" and company.email != to_email:
            if not company.website:
                company.website = "https://" + to_email.split("@")[1]
            company.email = to_email
            company.save()

        max_stage = Stage.objects.all().order_by("order").last()
        max_stage = max_stage.order if max_stage else 0

        job, created = Job.objects.update_or_create(
            company=company,
            role=role,
            defaults={
                'slug': slugify(role.title + "-at-" + company.name),
            }
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
            original_date = make_aware(original_date, timezone.get_default_timezone())


            if application.date_applied > original_date:
                application.date_applied = original_date
        if created:
            original_date = make_aware(original_date, timezone.get_default_timezone())


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
        et_offset = timedelta(hours=-4)

        now_server = timezone.now()

        now_et = now_server + et_offset

        start_time_et = datetime.combine(now_et.date(), time.min).replace(
            tzinfo=dt_timezone.utc
        )

        start_time_server = start_time_et - et_offset

        today_count = Application.objects.filter(
            user=request.user, created__gte=start_time_server
        ).count()

        data = {"email": email_data, "counts": stage_counts, "today_count": today_count}
        cache_key = f'detail_{company.id}_user_{request.user.id}'
        cache.delete(cache_key)

        return JsonResponse(data, status=status.HTTP_201_CREATED)


from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from requests.exceptions import RequestException

from .models import Application, Company, Job, Stage


class CompanyJobDetailView(DetailView):
    template_name = "company_detail.html"  # Single template for both

    def get_object(self):
        """
        Determine whether the slug is for a Job or Company based on the URL pattern.
        """
        slug = self.kwargs.get("slug")
        type = self.kwargs.get("type")

        if type == "job":
            obj = get_object_or_404(Job, slug=slug)
        elif type == "company":
            obj = get_object_or_404(Company, slug=slug)
        else:
            raise ValueError("Invalid type for URL")

        return obj

    def get_user_applications(self, jobs, user):
        """
        Fetch applications made by the current user for the jobs listed for the company.
        Attach the application to the job object.
        """
        if user.is_authenticated:
            applications = Application.objects.filter(job__in=jobs, user=user)
            application_map = {app.job_id: app for app in applications}
            for job in jobs:
                job.user_application = application_map.get(job.id)  # Attach application to the job object
        else:
            for job in jobs:
                job.user_application = None  # No application for anonymous users

    def get_common_data(self, obj):
        """
        Fetch and cache common data like applications, stages, and company/job info.
        """
        cache_key = f'detail_{obj.id}_user_{self.request.user.id if self.request.user.is_authenticated else "anonymous"}'
        cached_data = cache.get(cache_key)

        if not cached_data:
            cached_data = {"object": obj}
            if isinstance(obj, Job):
                cached_data["company"] = obj.company
            else:
                cached_data["company"] = obj

            if self.request.user.is_authenticated:
                if isinstance(obj, Job):
                    cached_data["applications"] = Application.objects.filter(job=obj, user=self.request.user)
                else:
                    cached_data["applications"] = Application.objects.filter(company=obj, user=self.request.user)

            cached_data["stages"] = Stage.objects.all().order_by("-order")
            cache.set(cache_key, cached_data, timeout=60 * 60 * 24 * 30)  # Cache for 30 days

        return cached_data

    def get_next_company(self, company):
        """
        Get the next company to display.
        """
        next_company_cache_key = f"cache_company_{company.id + 1}"
        next_company = cache.get(next_company_cache_key)
        if not next_company:
            next_company = Company.objects.filter(id__gt=company.id).first() or Company.objects.all().order_by("?").first()
            if next_company:
                cache.set(next_company_cache_key, next_company, timeout=60 * 60 * 24)  # Cache for 24 hours
        return next_company

    # def update_website_status(self, company):
    #     """
    #     Update the website status of the company.
    #     """
    #     website_status_cache_key = f"website_status_{company.id}"
    #     website_status_info = cache.get(website_status_cache_key)

    #     if not website_status_info:
    #         if not company.website_status_updated or (timezone.now() - company.website_status_updated).days >= 7:
    #             website = company.website or f"https://{company.slug}.com"
    #             try:
    #                 response = requests.get(website, timeout=10)
    #                 company.website_status_updated = timezone.now()
    #                 if not company.website and company.name.lower() in response.text.lower():
    #                     company.website = response.url
    #                 company.website_status = response.status_code
    #             except RequestException:
    #                 company.website_status = 500
    #                 company.website_status_updated = timezone.now()
    #             finally:
    #                 company.save(update_fields=["website", "website_status", "website_status_updated"])
    #                 website_status_info = {
    #                     "website_status": company.website_status,
    #                     "website_status_updated": company.website_status_updated,
    #                     "website": company.website,
    #                 }
    #                 cache.set(website_status_cache_key, website_status_info, timeout=60 * 60 * 24)

    #     return website_status_info

    def get_context_data(self, **kwargs):
        obj = self.get_object()
        context = super().get_context_data(**kwargs)
        common_data = self.get_common_data(obj)

        context.update(common_data)

        # If the object is a company, fetch the job list and user applications for those jobs
        if isinstance(obj, Company):
            jobs = obj.job_set.all()  # Get all jobs for the company
            self.get_user_applications(jobs, self.request.user)  # Attach user applications to jobs
            context['jobs'] = jobs
            context["next_company"] = self.get_next_company(obj)
            #context["website_status_info"] = self.update_website_status(obj)
        elif isinstance(obj, Job):
            company = obj.company
            jobs = company.job_set.all()
            self.get_user_applications(jobs, self.request.user)
            context['jobs'] = jobs
            context["next_company"] = self.get_next_company(obj.company)
            #context["website_status_info"] = self.update_website_status(obj.company)

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



from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (
    Avg,
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Prefetch,
    Q,
    Value,
)
from django.db.models.functions import Coalesce, TruncDay
from django.shortcuts import get_object_or_404
from django.utils.timezone import timedelta
from django.views.generic import ListView


class DashboardView(LoginRequiredMixin, ListView):
    template_name = "dashboard.html"
    context_object_name = "applications"
    paginate_by = 200

    def get_queryset(self):
        # Existing query setup...
        view_param = self.request.GET.get("view")
        sort_by = self.request.GET.get("sort_by", "last_email")
        sort_order = "asc" if "-" not in sort_by else "desc"
        order_prefix = "" if sort_order == "asc" else "-"
        user = self.request.user

        # Map sort fields...
        sort_fields = {
            "company": "company__name",
            "role": "job__title",
            "salary_max": "job__salary_max",
            "salary_min": "job__salary_min",
            "applied": "created",
            "last_email": "date_of_last_email",
        }

        if view_param == "resume_view":
            only_applied = self.request.GET.get("only_applied")
            if only_applied:
                applications = Application.objects.filter(
                    user=user,
                    stage__name="Applied"
                )
            else:
                applications = Application.objects.filter(user=user)
            applications = applications.annotate(
                resume_views=Count(
                    "company__requestlog",
                    filter=Q(company__requestlog__profile__user=user),
                )
            ).filter(resume_views__gt=0)
            today = timezone.now().date()
            applications = applications.annotate(
                days_since_last_email_sort=ExpressionWrapper(
                    Coalesce(F("date_of_last_email"), Value(today)) - Value(today),
                    output_field=DurationField(),
                )
            ).annotate(
                days_int=ExtractDay(F("days_since_last_email_sort"))
            ).order_by(f"{order_prefix}days_int")
            
        else:
            # Fetch applications by stage...
            stage_name = self.request.GET.get("stage", "Applied")
            stage_obj = get_object_or_404(Stage, name=stage_name)
            applications = Application.objects.filter(user=user, stage=stage_obj)

            # Annotate resume views...
            applications = applications.annotate(
                resume_views=Count(
                    "company__requestlog",
                    filter=Q(company__requestlog__profile__user=user),
                )
            )

            # Filter by selected date if provided...
            selected_date = self.request.GET.get("date")
            if selected_date:
                try:
                    parsed_date = datetime.strptime(selected_date, "%Y-%m-%d")
                    if is_naive(parsed_date):
                        parsed_date = make_aware(parsed_date)
                    applications = applications.filter(
                        date_applied__date=parsed_date.date()
                    )
                    sort_by = "-date_applied"
                except ValueError:
                    pass

            # Special sorting case for days and email...
            if sort_by == "days":
                today = timezone.now().date()
                applications = applications.annotate(
                    days_since_last_email=ExpressionWrapper(
                        Coalesce(F("date_of_last_email"), Value(today)) - Value(today),
                        output_field=DurationField(),
                    )
                ).annotate(
                    days_int=ExtractDay(F("days_since_last_email"))
                ).order_by(f"{order_prefix}days_int")
            elif sort_by == "email":
                applications = applications.annotate(email_count=Count("email")).order_by(
                    f"{order_prefix}email_count"
                )
            elif sort_by in sort_fields:
                applications = applications.order_by(f"{order_prefix}{sort_fields[sort_by]}")

        # Prefetch related objects...
        applications = applications.prefetch_related(
            Prefetch('company'), Prefetch('stage'), Prefetch('job'), 
            Prefetch('job__company'), Prefetch('job__role'), 
            Prefetch('email_set')
        )

        return applications

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Existing stage and job context setup...
        context["stages"] = Stage.objects.annotate(
            count=Count("application", filter=Q(application__user=user))
        ).order_by("-order")
        context["total_jobs"] = Job.objects.count()

        # Application days calculation (same as before)...
        applications_by_day = Application.objects.filter(user=user).annotate(
            date=TruncDay("date_applied")
        ).values("date").annotate(
            application_count=Count("id"),
            clicks_percent=ExpressionWrapper(
                (Count("email") * 100.0) / Count("id"), output_field=DecimalField()
            ),
            bounces_percent=ExpressionWrapper(
                Count(
                    "company__bouncedemail",
                    filter=Q(company__bouncedemail__created__date=F("date")),
                ) * 100.0 / Count("id"),
                output_field=DecimalField(),
            ),
        ).order_by("-date")

        # Emails sent per day calculation...
        emails_sent_by_day = Email.objects.filter(application__user=user).annotate(
            truncated_date=TruncDay("date")  # Avoid conflicting with the original 'date' field by using 'truncated_date'
        ).values("truncated_date").annotate(
            email_count=Count("id")
        ).order_by("-truncated_date")

        # Resume views by day calculation...
        resume_views_by_day = RequestLog.objects.filter(profile__user=user).annotate(
            date=TruncDay("created")
        ).values("date").annotate(
            views_count=Count("id")
        ).order_by("-date")

        # Grouping data into the application_days list...
        application_days_data = []
        for day in applications_by_day[:10]:
            # Find matching emails sent for the day
            email_day = next((email for email in emails_sent_by_day if email["truncated_date"] == day["date"]), None)
            email_count = email_day["email_count"] if email_day else 0

            # Find matching resume views for the day
            resume_view_day = next((view for view in resume_views_by_day if view["date"] == day["date"]), None)
            resume_view_count = resume_view_day["views_count"] if resume_view_day else 0

            # Append to the application_days_data list
            application_days_data.append({
                "date": day["date"],
                "count": day["application_count"],
                "clicks_percent": round(day["clicks_percent"], 2) if day["application_count"] > 0 else 0,
                "bounces_percent": round(day["bounces_percent"], 2) if day["application_count"] > 0 else 0,
                "emails_sent": email_count,
                "resume_views": resume_view_count,
            })

        context["application_days"] = application_days_data

        context["resume_views_total_companies"] = RequestLog.objects.filter(
            profile__user=user
        ).values("company").distinct().count()

        # Pass sorting and stage context...
        context["sort_by"] = self.request.GET.get("sort_by", "applied")
        context["sort_order"] = self.request.GET.get("sort_order", "desc")
        context["stage"] = self.request.GET.get("stage", "Scheduled")

        return context



from urllib.parse import urlparse


def normalize_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc or parsed_url.path
    if domain.startswith("www."):
        domain = domain[4:]

    return domain


@login_required
def update_company_email(request):
    email = request.GET.get("email")
    if email:
        domain = email.split("@")[-1].lower()
        try:
            companies = Company.objects.filter(website__icontains=domain)
            if not companies.exists():
                messages.error(request, "No company found with the specified domain of " + domain)
                return redirect("home")

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
                cache_key = f"detail_{matched_company.id}_user_{request.user.id}"
                cache.delete(cache_key)
                return redirect("company_detail", slug=matched_company.slug)
            else:
                company_list = ", ".join([company.name for company in companies])
                messages.error(
                    request,
                    "Multiple companies found with the specified domain, they were: "
                    + company_list,
                )
                return redirect("home")
        except Company.DoesNotExist:
            messages.error(request, "No company found with the specified domain.")
            return redirect("home")
            # return redirect(
            #     "company_list"
            # )  # Redirect to a list of companies or a suitable page

    else:
        messages.error(request, "No email address provided.")
        return redirect("home")
        #return redirect("company_list")


import re

from bs4 import BeautifulSoup  # To parse and correct HTML
from django.http import Http404, HttpResponse


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def home_view(request):
    return render(request, "home.html")


def resume_view(request, slug):
    if request.method == "GET":
        # Validate the slug to check if it matches the pattern YYYYMMDD-#
        is_slug_valid = re.match(r"^\d{8}-\d+$", slug)
        if is_slug_valid:
            try:
                profile = Profile.objects.get(resume_key=slug)
                if profile.user != request.user:
                    if not request.GET.get("e"):
                        raise Http404
                is_email_valid = re.match(r"[^@]+@[^@]+\.[^@]+", request.GET.get("e"))
                if is_email_valid:
                    email = request.GET.get("e")
                    company = (
                        Company.objects.filter(email=email)
                        .order_by("-modified")
                        .first()
                    )
                    # Find applications by user to that company
                    applications = Application.objects.filter(
                        user=profile.user, company=company
                    )
                    # If status = passed, then show 404
                    if not applications.exclude(stage__name="Passed").exists():
                        raise Http404

                    if not applications:
                        raise Http404

                    # Log the request to the Request table
                    RequestLog.objects.create(
                        profile=profile,
                        company=company,
                        email=request.GET.get("e"),
                        applications=applications.count(),
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get("HTTP_USER_AGENT"),
                        referer=request.META.get("HTTP_REFERER"),
                    )
                else:
                    if profile.user != request.user:
                        raise Http404

                user_email = profile.user.email
                html_resume = profile.html_resume

                # Use BeautifulSoup to ensure the HTML is valid and well-formed
                soup = BeautifulSoup(html_resume, "html.parser")

                # Remove <script> tags
                for script in soup(["script"]):
                    script.extract()

                # Remove inline event handlers
                for tag in soup.find_all(True):
                    for attr in list(tag.attrs):
                        if attr.startswith("on"):
                            del tag.attrs[attr]

                # Add target="_blank" to all <a> tags and increase z-index
                for a_tag in soup.find_all("a"):
                    a_tag["target"] = "_blank"
                    a_tag["style"] = (
                        "z-index: 1002; position: relative;"  # Higher z-index than the overlay
                    )

                if not soup.body:
                    if soup.html:
                        soup.html.append(soup.new_tag("body"))
                    else:
                        soup = BeautifulSoup(
                            "<html><body></body></html>", "html.parser"
                        )
                        soup.body.append(BeautifulSoup(str(soup), "html.parser"))

                # Add an overlay to prevent right-clicking and copying
                overlay = soup.new_tag(
                    "div",
                    style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0); z-index: 1000;",
                )
                soup.body.append(overlay)
                if profile.user != request.user:
                    if applications.filter(~Q(stage__name="Applied")).exists():

                        # Add a centered sticky div at the bottom for interview options
                        sticky_div = soup.new_tag(
                            "div",
                            style="position: fixed; bottom: 10px; left: 50%; transform: translateX(-50%); background-color: #f9f9f9; padding: 20px; border: 2px solid #ccc; box-shadow: 0px 0px 15px rgba(0,0,0,0.1); z-index: 1001; text-align: center; border-radius: 10px; width: auto; max-width: 90%;",
                        )

                        prompt = soup.new_tag("p", style="margin: 0 0 10px; font-size: 1.2em;")
                        prompt.string = (
                            f"Would you like to interview {profile.user.first_name}?"
                        )
                        sticky_div.append(prompt)

                        button_style = "margin: 0 10px; padding: 10px 20px; background-color: #1a73e8; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 1em;"

                        yes_button = soup.new_tag("button", id="yesButton", style=button_style)
                        yes_button.string = "Yes"
                        sticky_div.append(yes_button)

                        no_button = soup.new_tag("button", id="noButton", style=button_style)
                        no_button.string = "No"
                        sticky_div.append(no_button)

                        # Reason field (initially hidden)
                        reason_div = soup.new_tag(
                            "div", id="reasonField", style="display:none; margin-top: 10px;"
                        )
                        reason_prompt = soup.new_tag(
                            "p", style="margin: 0 0 10px; font-size: 1em;"
                        )
                        reason_prompt.string = "Please provide a reason:"
                        reason_div.append(reason_prompt)
                        reason_textarea = soup.new_tag(
                            "textarea",
                            id="reasonText",
                            rows="3",
                            cols="50",
                            placeholder="Enter reason here...",
                            style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #ccc;",
                        )
                        reason_div.append(reason_textarea)

                        submit_reason_button = soup.new_tag(
                            "button", id="submitReasonButton", style=button_style
                        )
                        submit_reason_button.string = "Submit Reason"
                        reason_div.append(submit_reason_button)

                        close_button = soup.new_tag(
                            "button", id="closeButton", style=button_style
                        )
                        close_button.string = "Close"
                        reason_div.append(close_button)

                        sticky_div.append(reason_div)

                        # Interview options (initially hidden)
                        interview_options = soup.new_tag(
                            "div",
                            id="interviewOptions",
                            style="display:none; margin-top: 10px;",
                        )
                        options_prompt = soup.new_tag(
                            "p", style="margin: 0 0 10px; font-size: 1em;"
                        )
                        options_prompt.string = "Choose an action:"
                        interview_options.append(options_prompt)

                        option_button_style = "margin: 5px 10px; padding: 10px 15px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 1em;"

                        # Create email link
                        email_button = soup.new_tag(
                            "button", id="emailButton", style=option_button_style
                        )
                        email_button.string = "Email"
                        email_link = f"https://mail.google.com/mail/?view=cm&fs=1&to={user_email}&su=Interview Request"
                        email_button["data-email-link"] = email_link
                        interview_options.append(email_button)

                        calendar_button = soup.new_tag(
                            "button", id="calendarButton", style=option_button_style
                        )
                        calendar_button.string = "Create Calendar Event"
                        calendar_link = f"https://calendar.google.com/calendar/u/0/r/eventedit?add={user_email}"
                        calendar_button["data-calendar-link"] = calendar_link
                        interview_options.append(calendar_button)

                        sticky_div.append(interview_options)

                        # Add a link to /accounts/profile/ on the bottom of the sticky div only if the user is the owner of the profile
                        if profile.user == request.user:
                            profile_link = soup.new_tag(
                                "a",
                                href="/accounts/profile/",
                                style="color: #1a73e8; font-size: 0.8em; text-decoration: none;",
                            )
                            profile_link.string = "Edit Profile"
                            sticky_div.append(profile_link)

                        soup.body.append(sticky_div)

                        # Add padding to the body to account for the sticky footer height
                        padding_div = soup.new_tag("div", style="padding-bottom: 120px;")
                        soup.body.append(padding_div)

                # Add JavaScript for disabling copy-paste and button functionality
                script = soup.new_tag("script")
                try:
                    application_id = applications.first().id
                except:
                    application_id = 0

                script.string = f"""
                document.addEventListener('keydown', function(event) {{
                    if ((event.ctrlKey || event.metaKey) && (event.key === 'c' || event.key === 'a')) {{
                        event.preventDefault();
                    }}
                }});

                document.addEventListener('contextmenu', function(event) {{
                    event.preventDefault();
                }});

                document.addEventListener('selectstart', function(event) {{
                    event.preventDefault();
                }});

                document.getElementById('yesButton').addEventListener('click', function() {{
                    document.getElementById('interviewOptions').style.display = 'block';
                    document.getElementById('reasonField').style.display = 'none';
                }});

                document.getElementById('noButton').addEventListener('click', function() {{
                    document.getElementById('reasonField').style.display = 'block';
                    document.getElementById('interviewOptions').style.display = 'none';
                }});

                document.getElementById('emailButton').addEventListener('click', function() {{
                    const emailLink = document.getElementById('emailButton').getAttribute('data-email-link');
                    window.open(emailLink, '_blank');
                }});

                document.getElementById('calendarButton').addEventListener('click', function() {{
                    const calendarLink = document.getElementById('calendarButton').getAttribute('data-calendar-link');
                    window.open(calendarLink, '_blank');
                }});

                document.getElementById('submitReasonButton').addEventListener('click', function() {{
                    const reason = document.getElementById('reasonText').value;
                    const applicationId = '{application_id}';

                    if (reason.trim() !== '') {{
                        fetch('/mark-application-as-passed/', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/x-www-form-urlencoded',
                                'X-CSRFToken': getCookie('csrftoken')
                            }},
                            body: `application_id=${{applicationId}}&reason=${{encodeURIComponent(reason)}}`
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                alert('Application marked as passed with reason.');
                            }} else {{
                                alert('Error: ' + (data.error || 'Unknown error occurred.'));
                            }}
                        }});
                    }} else {{
                        alert('Please provide a reason before submitting.');
                    }}
                }});

                function getCookie(name) {{
                    let cookieValue = null;
                    if (document.cookie && document.cookie !== '') {{
                        const cookies = document.cookie.split(';');
                        for (let i = 0; i < cookies.length; i++) {{
                            const cookie = cookies[i].trim();
                            if (cookie.substring(0, name.length + 1) === (name + '=')) {{
                                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                                break;
                            }}
                        }}
                    }}
                    return cookieValue;
                }}

                document.getElementById('closeButton').addEventListener('click', function() {{
                    document.getElementById('interviewOptions').style.display = 'none';
                    document.getElementById('reasonField').style.display = 'none';
                    document.getElementById('reasonText').value = '';

                    window._mfq = window._mfq || [];
                    (function() {{
                        var mf = document.createElement('script');
                        mf.type = 'text/javascript'; mf.defer = true;
                        mf.src = '//cdn.mouseflow.com/projects/75696671-ed61-4656-9ca3-1a503dc1d0b1.js';
                        document.getElementsByTagName("head")[0].appendChild(mf);
                    }})();
                }});
                """

                soup.body.append(script)

                return HttpResponse(str(soup))
            except Profile.DoesNotExist:
                raise Http404("Resume not found")
        else:
            raise Http404(f"Invalid slug {slug}")


@csrf_exempt
@require_POST
def mark_application_as_passed(request):
    application_id = request.POST.get("application_id")
    reason = request.POST.get("reason")

    if not application_id or not reason:
        return JsonResponse(
            {"error": "Application ID and reason are required."}, status=400
        )

    try:
        application = Application.objects.get(id=application_id)
        application.stage.name = "Passed"
        application.reason = reason + " (marked as passed from company)"
        application.save()
        # email the user
        send_mail(
            "Application marked as passed",
            f"Your application for the role of {application.job.role.title} at {application.company.name} has been marked as passed. Reason: {reason}",
            [settings.DEFAULT_FROM_EMAIL],
            [application.user.email],
            fail_silently=False,
        )

        return JsonResponse({"success": True})
    except Application.DoesNotExist:
        return JsonResponse({"error": "Application not found."}, status=404)


def model_counts_view(request):
    # Get counts for each model
    total_users = User.objects.count()
    total_profiles = Profile.objects.count()
    total_links = Link.objects.count()
    total_prompts = Prompt.objects.count()
    skills = Skill.objects.all()
    total_skills = skills.count()
    total_companies = Company.objects.count()
    total_roles = Role.objects.count()
    total_jobs = Job.objects.count()
    total_applications = Application.objects.count()
    total_searches = Search.objects.count()
    total_sources = Source.objects.count()
    total_emails = Email.objects.count()
    total_bounces = BouncedEmail.objects.count()

    user_data = {}

    # Check if the user is logged in
    if request.user.is_authenticated:
        user_data["user_prompts"] = Prompt.objects.filter(user=request.user).count()
        user_data["user_applications"] = Application.objects.filter(
            user=request.user
        ).count()
        user_data["user_skills"] = request.user.skills.count()
        user_data["user_links"] = (
            Profile.objects.get(user=request.user).links.count()
            if Profile.objects.filter(user=request.user).exists()
            else 0
        )
        user_data["user_roles"] = (
            Profile.objects.get(user=request.user).roles.count()
            if Profile.objects.filter(user=request.user).exists()
            else 0
        )
        user_data["user_emails"] = Email.objects.filter(
            application__user=request.user
        ).count()

    context = {
        "total_users": total_users,
        "total_profiles": total_profiles,
        "total_links": total_links,
        "total_prompts": total_prompts,
        "total_skills": total_skills,
        "total_companies": total_companies,
        "total_roles": total_roles,
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "total_searches": total_searches,
        "total_sources": total_sources,
        "total_emails": total_emails,
        "total_bounces": total_bounces,
        "user_data": user_data,
        "skills": skills,
    }

    return render(request, "model_counts.html", context)
