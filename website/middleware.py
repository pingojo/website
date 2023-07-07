
from django.shortcuts import render
import re
from django.http import HttpResponseForbidden
from urllib.parse import urlparse
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

        if request.method == 'POST':
            referer = request.META.get('HTTP_REFERER')
            if referer is not None:
                referer_hostname = urlparse(referer).hostname
                allowed_origins = [
                    "mail.google.com",
                    "pingojo.com",
                    "localhost",
                    "localhost:8000",
                    "127.0.0.1",
                    "127.0.0.1:8000",
                    "boards.greenhouse.io",
                    "boards.eu.greenhouse.io",
                    "wellfound.com",
                    "pythoncodingjobs.com",
                ]

                if referer_hostname not in allowed_origins and not re.match(r'https://\w+\.applytojob\.com', referer):
                    return HttpResponseForbidden()

        response = self.get_response(request)

        return response
