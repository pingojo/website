from django.contrib import admin
from .models import Skill, Company, Role, Job, Stage, Email, Application, Search, Source

class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'job_count', 'resume_count', 'web_views')
    prepopulated_fields = {'slug': ('name',)}

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'twitter_url', 'greenhouse_url', 'lever_url', 'number_of_employees_min', 'number_of_employees_max', 'description', 'website', 'city', 'state', 'country', 'ceo', 'ceo_twitter')
    search_fields = ('name', 'city', 'state', 'country', 'ceo')
    prepopulated_fields = {'slug': ('name',)}


class RoleAdmin(admin.ModelAdmin):
    list_display = ('title', 'job_count', 'resume_count', 'web_views')
    prepopulated_fields = {'slug': ('title',)}

class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'role', 'company', 'job_type', 'posted_date', 'closing_date', 'is_active')
    prepopulated_fields = {'slug': ('title',)}

class StageAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')

class EmailAdmin(admin.ModelAdmin):
    list_display = ('from_email', 'gmail_id', 'application', 'date')

class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'job', 'date_applied', 'stage', 'date_of_last_email', 'recruiter', 'email')

class SearchAdmin(admin.ModelAdmin):
    list_display = ('query', 'matched_job_count', 'matched_company_count', 'matched_skill_count', 'matched_role_count')

class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'url_structure', 'job_count')
    search_fields = ('name',)
    list_filter = ('website',)
    ordering = ('name',)

admin.site.register(Source, SourceAdmin)
admin.site.register(Skill, SkillAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Stage, StageAdmin)
admin.site.register(Email, EmailAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Search, SearchAdmin)
