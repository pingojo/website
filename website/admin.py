from django.contrib import admin
from .models import Skill, Company, Role, Job, Stage, Email, Application, Search, Source
from django.urls import path
from .admin_actions import merge_companies_action
from django.db.models import Count


class CompanyAdmin(admin.ModelAdmin):
    actions = [merge_companies_action]
    list_display = (
        "name",
        "slug",
        "twitter_url",
        "greenhouse_url",
        "lever_url",
        "number_of_employees_min",
        "number_of_employees_max",
        "description",
        "website",
        "city",
        "state",
        "country",
        "ceo",
        "ceo_twitter",
    )
    search_fields = ("name", "city", "state", "country", "ceo")
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
    search_fields = ("title", "company__name")


    list_display = (
        "id",
        "title",
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
    list_display = (
        "from_email",
        "to_email",
        "reply_to",
        "subject",
        "gmail_id",
        "application",
        "date",
    )


class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "company",
        "job",
        "date_applied",
        "stage",
        "date_of_last_email",
        "recruiter",
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


admin.site.register(Source, SourceAdmin)
admin.site.register(Skill, SkillAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Stage, StageAdmin)
admin.site.register(Email, EmailAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Search, SearchAdmin)
