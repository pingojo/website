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

@register.filter
def keyvalue(dict, key):
    new_dict = dict.copy()
    new_dict[key] = key
    return new_dict

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def replace_search_term(url, search_query):
    return url.replace('search_term', search_query)




@register.simple_tag
def url_modify(request, **kwargs):
    updated = request.GET.copy()
    for k, v in kwargs.items():
        updated[k] = v
    return updated.urlencode()


@register.simple_tag
def url_toggle_order(request, field):
    dict_ = request.GET.copy()

    if 'ordering' in dict_:
        if dict_['ordering'] == field:
            dict_['ordering'] = '-' + field
        else:
            dict_['ordering'] = field
    else:
        dict_['ordering'] = field

    return dict_.urlencode()
