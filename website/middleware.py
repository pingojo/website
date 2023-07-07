
from django.shortcuts import render

import re
from django.http import HttpResponseForbidden

class CustomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        return render(request, 'website/loading_page.html')
    

class CustomCsrfMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        referer = request.META.get('HTTP_REFERER')
        if referer is not None and not re.match(r'https://\w+\.applytojob\.com', referer):
            # If the referer is set and does not match the trusted pattern, return a 403 response.
            return HttpResponseForbidden()

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
