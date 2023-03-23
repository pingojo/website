from django.conf.urls import include
from django.urls import path, register_converter
from django.contrib import admin
from website.views import DashboardView, DisplayResumeView, Index, ApplicationView, ResumeUploadView
from website.utils import HashIdConverter
from django.views.generic.base import RedirectView

import os
from website import views

register_converter(HashIdConverter, "hashid")

admin.autodiscover()
app_name = 'pingojo'


def trigger_error(request):
    division_by_zero = 1 / 0

favicon_view = RedirectView.as_view(url='/static/img/favicon.ico', permanent=True)

urlpatterns = [
    path("", Index.as_view(), name="index"),
    path('company/<slug:slug>/', views.CompanyDetailView.as_view(), name='company_detail'),
    path('company/<slug:slug>/add_job_link/', views.add_job_link, name='add_job_link'),
    path("dashboard/", DashboardView.as_view(), name='dashboard'),
    path(os.environ.get("ADMIN_URL","admin/"), admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path('update_website_status/', views.UpdateWebsiteStatusView.as_view(), name='update_website_status'),
    path('sentry-debug/', trigger_error),
    path('scrape-job/', views.scrape_job, name='scrape-job'),
    path('search/', views.search, name='search'),
    path('job/<slug:slug>/', views.JobDetailView.as_view(), name='job_detail'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('favicon.ico', favicon_view),
    path('api/application/', ApplicationView.as_view(), name='application_view'),
    path('display_resume/', DisplayResumeView.as_view(), name='display_resume'),
    path('upload_resume/', ResumeUploadView.as_view(), name='upload_resume'),

]
