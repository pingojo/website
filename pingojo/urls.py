from django.conf.urls import include
from django.urls import path, register_converter
from django.contrib import admin
from website.views import (
    DashboardView,
    DisplayResumeView,
    AddJobLink,
    Index,
    ApplicationView,
    ResumeUploadView,
    CompanyListView,
    SourceListView,

)
from website.utils import HashIdConverter
from django.views.generic.base import RedirectView

import os
from website import views

from django.conf import settings
from django.conf.urls.static import static

register_converter(HashIdConverter, "hashid")

admin.autodiscover()
app_name = "pingojo"
import debug_toolbar

def trigger_error(request):
    division_by_zero = 1 / 0


favicon_view = RedirectView.as_view(url="/static/img/favicon.ico", permanent=True)

urlpatterns = [
    path("", Index.as_view(), name="index"),
    path(
        "company/<slug:slug>/", views.CompanyDetailView.as_view(), name="company_detail"
    ),
    path("company/<slug:slug>/add_job_link/", views.add_job_link, name="add_job_link"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path(os.environ.get("ADMIN_URL", "admin/"), admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("sentry-debug/", trigger_error),
    path("scrape-job/", views.scrape_job, name="scrape-job"),
    path("search/", views.search, name="search"),
    path("job/<slug:slug>/", views.JobDetailView.as_view(), name="job_detail"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("terms-of-service/", views.terms_of_service, name="terms_of_service"),
    path("favicon.ico", favicon_view),
    path("api/application/", ApplicationView.as_view(), name="application_view"),
    path("api/add_job/", AddJobLink.as_view(), name="add_job_view"),
    path("display_resume/", DisplayResumeView.as_view(), name="display_resume"),
    path("upload_resume/", ResumeUploadView.as_view(), name="upload_resume"),
    path(
        "update_application_stage/",
        views.update_application_stage,
        name="update-application-stage",
    ),
    path("job_add/", views.job_add, name="job_add"),
    path("autocomplete/<str:model>/", views.autocomplete, name="autocomplete"),
    path('company_list/', CompanyListView.as_view(), name='company_list'),
    path('sources/', SourceListView.as_view(), name='source-list'),
    path('jobs/', views.JobListView.as_view(), name='jobs_list'),
    #path('challenge/', views.JobListView.as_view(), name='challenge'),
    path('update-application-link/', views.update_application_link, name='update_application_link'),
    path('job_application_delete/<int:application_id>', views.job_application_delete, name='job_application_delete'),
    path('update_email/', views.update_email, name='update_email'),
    path('update_company/<int:company_id>', views.update_company, name='update_company'),
    path('update_job/<int:job_id>', views.update_job, name='update_job'),
    #path('generage_follow_up_email/<int:application_id>', views.generage_follow_up_email, name='generage_follow_up_email'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.ENABLE_DEBUG_TOOLBAR:
    
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns