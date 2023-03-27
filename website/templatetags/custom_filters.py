# your_app/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def filter_stage(application, stage):
    return [application for application in application if application.stage.name == stage]