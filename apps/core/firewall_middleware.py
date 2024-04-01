import os
from django.http import HttpResponseForbidden


class FirewallMiddleware:
    """
    Middleware to restrict access to the application based on allow listed IPs.
    """

    # List of allowed IP addresses, loaded from ALLOWED_IPS environment variable and split by comma:
    ALLOWED_IPS = os.environ.get('ALLOWED_IPS', '127.0.0.1').split(',')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Attempt to get the client's real IP address if behind a proxy
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]  # Take the first IP from the list
        else:
            ip = request.META.get('REMOTE_ADDR')  # Fallback to REMOTE_ADDR if X-Forwarded-For is not available

        # Check if the IP is allowed
        if ip not in self.ALLOWED_IPS:
            return HttpResponseForbidden('Forbidden')

        response = self.get_response(request)
        return response
