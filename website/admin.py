from allauth.account.models import EmailConfirmation
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Count
from django.template import Context, Template
from django.template.response import TemplateResponse
from django.urls import path

from .admin_actions import merge_companies_action
from .models import (
    Application,
    BouncedEmail,
    Company,
    Email,
    Job,
    Link,
    Profile,
    Prompt,
    RequestLog,
    Role,
    Search,
    Skill,
    Source,
    Stage,
)


class CompanyAdmin(admin.ModelAdmin):
    actions = [merge_companies_action]
    list_display = (
        "id",
        "name",
        "slug",        
        "website",
        "email",
    )
    search_fields = ("name", "city", "state", "country", "ceo", "email")
    prepopulated_fields = {"slug": ("name",)}

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "merge_companies/",
                self.admin_site.admin_view(merge_companies_action),
                name="merge_companies",
            ),
        ]
        return custom_urls + urls


class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "job_count", "resume_count", "web_views")
    prepopulated_fields = {"slug": ("name",)}


class RoleAdmin(admin.ModelAdmin):
    list_display = ("title", "job_count", "resume_count", "web_views")
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}


class JobAdmin(admin.ModelAdmin):
    search_fields = ("title", "company__name", "slug", "location")
    raw_id_fields = ("company", "role")

    list_display = (
        "id",
        "title",
        "slug",
        "role",
        "application_count",
        "company",
        "job_type",
        "salary_min",
        "salary_max",
        "posted_date",
        "closing_date",
        "link",
        "link_status_code",
        "location",
        "equity_min",
        "equity_max",
        "remote",
    )

    prepopulated_fields = {"slug": ("title",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(application_count=Count("application"))
        return qs

    def application_count(self, obj):
        return obj.application_count


class StageAdmin(admin.ModelAdmin):
    list_display = ("name", "order")


class EmailAdmin(admin.ModelAdmin):
    raw_id_fields = ("application",)

    def get_user_username(self, obj):
        # Accessing the user's username through the application object
        return obj.application.user.username

    get_user_username.short_description = "Username"  # Optional: Sets a column header

    list_display = (
        "get_user_username",
        "gmail_id",
        # "application",
        "date",
    )


class ApplicationAdmin(admin.ModelAdmin):
    raw_id_fields = ("company", "job")
    list_display = (
        "user",
        "company",
        "job",
        "date_applied",
        "stage",
        "date_of_last_email",
        "recruiter",
        "created",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "company__name",
        "job__title",
    )


class SearchAdmin(admin.ModelAdmin):
    list_display = (
        "query",
        "matched_job_count",
        "matched_company_count",
        "matched_skill_count",
        "matched_role_count",
        "created",
    )


class SourceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "website",
        "search_url",
        "google_result_count",
        "url_structure",
        "job_count",
    )
    search_fields = ("name",)
    list_filter = ("website",)
    list_editable = ("website", "search_url")
    ordering = ("name",)


class UserAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "date_joined",
        "last_login",
    )
    actions = ["send_EMAIL", "create_user_profile"]
    search_fields = ["username", "email"]

    def create_user_profile(self, request, queryset):
        for user in queryset:
            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                messages.info(request, f"Profile created for {user.username}")
            else:
                messages.warning(request, f"Profile already exists for {user.username}")

    create_user_profile.short_description = "Create user profile if not exists"

    def send_EMAIL(self, request, queryset):
        if request.POST.get("post"):
            for x in queryset:
                user = User.objects.get(username=x)
                c = Context(
                    {
                        "email": request.POST.get("email", user.email),
                    }
                )
                t = Template(request.POST.get("body"))

                send_mail(
                    request.POST.get("subject"),
                    t.render(c),
                    "Pingojo <" + settings.DEFAULT_FROM_EMAIL + ">",
                    [request.POST.get("email", user.email)],
                    fail_silently=False,
                )
            messages.success(request, "emails have been sent")
        else:
            context = {
                "title": "Are you sure?",
                "queryset": queryset,
                "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
            }
            return TemplateResponse(request, "email.html", context)


@admin.register(EmailConfirmation)
class EmailConfirmationAdmin(admin.ModelAdmin):
    list_display = [field.name for field in EmailConfirmation._meta.get_fields()]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "resume",
        "bio",
        "profile_picture",
        "resume_views",
        "web_views",
        "resume_download_count",
        "resume_download_limit",
        "is_public",
    ]
    # to speed things up keep certain fields out
    fields = (
        "user",
        "resume",
        "bio",
        "profile_picture",
        "resume_views",
        "web_views",
        "resume_download_count",
        "resume_download_limit",
        "is_public",
        "html_resume",
        "resume_key",
    )


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Link._meta.get_fields()]

@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "applications",
        "ip_address",
        "user_agent",
        "referer",
        "created",
    ]
@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "content",
        "created",
    ]
@admin.register(BouncedEmail)
class BounceAdmin(admin.ModelAdmin):
    list_display = [
        "company",
        "email",
        "reason",
        "created",
    ]
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Source, SourceAdmin)
admin.site.register(Skill, SkillAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Stage, StageAdmin)
admin.site.register(Email, EmailAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Search, SearchAdmin)
