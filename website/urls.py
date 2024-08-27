import os

import debug_toolbar
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, register_converter
from django.views.generic.base import RedirectView

from website import views
from website.utils import HashIdConverter
from website.views import (  # CompanyListView,
    AddJobLink,
    ApplicationView,
    BouncedEmailAPI,
    DashboardView,
    DisplayResumeView,
    GetCompanyEmailView,
    ProfileListView,
    ResumeUploadView,
    SourceListView,
)

register_converter(HashIdConverter, "hashid")

admin.autodiscover()
app_name = "pingojo"

favicon_view = RedirectView.as_view(url="/static/img/favicon.ico", permanent=True)

urlpatterns = [
    path("", views.JobListView.as_view(), name="jobs_list"),
    path(
        "company/<slug:slug>/", views.CompanyDetailView.as_view(), name="company_detail"
    ),
    path("home/", views.home_view, name="home"),
    path("resume/<slug:slug>/", views.resume_view, name="resume"),
    path("mark-application-as-passed/", views.mark_application_as_passed, name="mark_application_as_passed"),
    path('model-counts/', views.model_counts_view, name='model-counts'),
    path("company/<slug:slug>/add_job_link/", views.add_job_link, name="add_job_link"),
    path("add_email/", views.update_company_email, name="add_email"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path(os.environ.get("ADMIN_URL", "admin/"), admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("scrape-job/", views.scrape_job, name="scrape-job"),
    # path("search/", views.search, name="search"),
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
    #path("company_list/", CompanyListView.as_view(), name="company_list"),
    path("sources/", SourceListView.as_view(), name="source-list"),
    # path('challenge/', views.JobListView.as_view(), name='challenge'),
    path(
        "update-application-link/",
        views.update_application_link,
        name="update_application_link",
    ),
    path(
        "job_application_delete/<int:application_id>",
        views.job_application_delete,
        name="job_application_delete",
    ),
    path("update_email/", views.update_email, name="update_email"),
    path(
        "update_company/<int:company_id>", views.update_company, name="update_company"
    ),
    path("update_job/<int:job_id>", views.update_job, name="update_job"),
    # path('generage_follow_up_email/<int:application_id>', views.generage_follow_up_email, name='generage_follow_up_email'),
    path("api/is_authenticated", views.is_authenticated, name="is_authenticated"),
    path("api/bounced_email/", BouncedEmailAPI.as_view(), name="bounced_email"),
    path('edit-note/<int:application_id>/', views.edit_note_view, name='edit_note'),
    path('resume_clicks/<int:company_id>/', views.view_resume_clicks, name='view_resume_clicks'),
    path("accounts/profile/", views.profile_view, name="profile"),
    path("job_detail_htmx/<slug:slug>/", views.job_detail_htmx, name="job_detail_htmx"),
    path("pricing/", views.pricing, name="pricing"),
    path("donate/", views.donate, name="donate"),
    path(
        "accounts/profile/<int:prompt_id>/",
        views.profile_view,
        name="profile_with_prompt",
    ),
    path("api/application_count/", views.application_count, name="application_count"),
    path("captcha/", include("captcha.urls")),
    path("profiles/", ProfileListView.as_view(), name="profile-list"),
    path("skills/search/", views.skill_search, name="skill_search"),
    path("skills/update/", views.update_skills, name="update_skills"),
    path("skills/delete/<int:skill_id>", views.delete_skill, name="delete_skill"),
    path("role/search/", views.role_search, name="role_search"),
    path("role/update/", views.update_roles, name="update_roles"),
    path("role/delete/<int:role_id>", views.delete_role, name="delete_role"),
    path("link/delete/<int:link_id>", views.delete_link, name="delete_link"),
    path("<str:username>/", views.profile, name="profile"),
    path(
        "api/get_company_email/",
        GetCompanyEmailView.as_view(),
        name="get_company_email",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.ENABLE_DEBUG_TOOLBAR:
    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
