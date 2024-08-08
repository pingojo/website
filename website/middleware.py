from django.http import HttpResponseForbidden


class BlockUserAgentsMiddleware:
    # List of blocked user-agent strings
    BLOCKED_USER_AGENTS = ["DotBot", "SemrushBot", "crawler", "PetalBot", "Bytespider"]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        for blocked_agent in self.BLOCKED_USER_AGENTS:
            if blocked_agent in user_agent:
                return HttpResponseForbidden()  # Reject the request with a 403 Forbidden status

        response = self.get_response(request)
        return response
