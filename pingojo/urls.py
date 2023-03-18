from django.conf.urls import include
from django.urls import path, register_converter
from django.contrib import admin
from website.views import ApplicationDetailView, Dashboard, Index, ApplicationView
from django.contrib.auth.decorators import login_required
from website.utils import HashIdConverter

import os

register_converter(HashIdConverter, "hashid")

admin.autodiscover()

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
    path("dashboard/", Dashboard.as_view()),
    path(os.environ.get("ADMIN_URL","admin/"), admin.site.urls),
    path("accounts/", include("allauth.urls")),
]
