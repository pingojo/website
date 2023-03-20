from django.conf.urls import include
from django.urls import path, register_converter
from django.contrib import admin
from website.views import ApplicationDetailView, DashboardView, Index, ApplicationView
from django.contrib.auth.decorators import login_required
from website.utils import HashIdConverter

import os
from website import views

register_converter(HashIdConverter, "hashid")

admin.autodiscover()
app_name = 'pingojo'


def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [
    path("", Index.as_view(), name="index"),
    path(
        "application/",
        login_required(ApplicationView.as_view()),
        name="application",
    ),
    path(
        "application/<hashid:pk>",
        login_required(ApplicationDetailView.as_view()),
        name="application-detail",
    ),
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

]
