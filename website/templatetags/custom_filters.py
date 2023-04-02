# your_app/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def filter_stage(application, stage):
    return [application for application in application if application.stage.name == stage]


@register.filter
def dict_key(d, k):
    """Returns the given key from a dictionary."""
    return d.get(k)