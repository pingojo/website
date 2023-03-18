from website.utils import get_website_title
from django.views.generic.detail import DetailView
from website.models import Application
from django.views.generic.base import TemplateView
from django.views.generic import ListView, CreateView
from django.utils import timezone
from django.views import generic
from .models import Company
from django.shortcuts import get_object_or_404, redirect
from .models import Job
import random

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


class Dashboard(ListView):
    pass


class Index(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companies = list(Company.objects.all())
        random.shuffle(companies)
        context['companies'] = companies[:50]
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