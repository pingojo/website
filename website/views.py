from website.utils import get_website_title, send_slack_notification
from django.views.generic.detail import DetailView
from website.models import Application
from django.views.generic.base import TemplateView
from django.views.generic import ListView, CreateView
from django.utils import timezone
from django.utils import timezone

from django.views import generic

from django.shortcuts import get_object_or_404, redirect
from .models import Job, Search
import random
from django.views import View
from django.http import JsonResponse
from .models import Company, Stage
from datetime import datetime

from django.shortcuts import render
from .models import Job

# views.py
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

class JobDetailView(DetailView):
    model = Job
    template_name = 'job_detail.html'
    context_object_name = 'job'

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def terms_of_service(request):
    return render(request, 'terms_of_service.html')


def search(request):
    search_query = request.GET.get('search', '')

    if search_query:
        jobs = Job.objects.filter(
            Q(title__icontains=search_query) |
            Q(company__name__icontains=search_query)
        )
        companies = Company.objects.filter(
            name__icontains=search_query
        )
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

    # Paginate jobs
    jobs_paginator = Paginator(jobs, 10)  # Show 10 jobs per page
    jobs_page = request.GET.get('jobs_page', 1)
    paginated_jobs = jobs_paginator.get_page(jobs_page)

    # Paginate companies
    companies_paginator = Paginator(companies, 10)  # Show 10 companies per page
    companies_page = request.GET.get('companies_page', 1)
    paginated_companies = companies_paginator.get_page(companies_page)

    return render(request, 'search.html', {
        'paginated_jobs': paginated_jobs,
        'paginated_companies': paginated_companies,
        'search_query': search_query,
    })


def scrape_job(request):
    url = request.GET.get('url', '')
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    # Parse the job details here
    # job_title = ...
    # company_name = ...
    return JsonResponse({'job_title': job_title, 'company_name': company_name})


class DashboardView(LoginRequiredMixin, ListView):
    template_name = 'dashboard.html'
    context_object_name = 'applications'

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stages'] = Stage.objects.all()
        return context

class ApplicationView(CreateView):
    model = Application
    fields = ["input"]

    def form_valid(self, form):
        form.instance.user = self.request.user
        print(form.instance.id)
        form.instance.reference_id = form.instance.id
        return super(ApplicationView, self).form_valid(form)


class ApplicationDetailView(DetailView):
    model = Application

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()
        context["title"] = get_website_title(self.get_object().input)
        return context



class Index(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_companies = Company.objects.all()
        companies = list(all_companies)
        random.shuffle(companies)
        context['companies'] = companies[:50]
        context['company_count'] = all_companies.count()
        return context
    
class CompanyDetailView(generic.DetailView):
    model = Company
    template_name = 'company_detail.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Company, slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_company = self.get_object()
        prev_company = Company.objects.filter(name__lt=current_company.name).order_by('-name').first()
        next_company = Company.objects.filter(name__gt=current_company.name).order_by('name').first()
        context['prev_company'] = prev_company
        context['next_company'] = next_company
        return context


def add_job_link(request, slug):
    company = get_object_or_404(Company, slug=slug)
    if request.method == 'POST':
        job_link = request.POST.get('job_link')
        job = Job(link=job_link, company=company)
        job.save()
        return redirect('company_detail', slug=slug)
    



import requests
from django.views import View
from django.http import JsonResponse
from .models import Company
from datetime import datetime, timedelta

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
        company_id = request.GET.get('company_id')
        company = self.get_company(company_id)
        if not company:
            return JsonResponse({'status': 'error', 'message': 'Company not found'}, status=404)

        if (not company.website_status_updated or 
                (datetime.now() - company.website_status_updated).days >= 7):
            response = requests.get(company.website)
            self.update_status(company, response.status_code)

        return JsonResponse({'status': 'success', 'website_status': company.website_status})

    def post(self, request, *args, **kwargs):
        company_id = request.POST.get('company_id')
        status = request.POST.get('status')

        company = self.get_company(company_id)
        if not company:
            return JsonResponse({'status': 'error', 'message': 'Company not found'}, status=404)

        self.update_status(company, int(status))
        return JsonResponse({'status': 'success'})

