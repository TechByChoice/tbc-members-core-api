# /path/to/middleware.py

from django.http import HttpResponseForbidden

class FirewallMiddleware:
    """
    Middleware to restrict access to the application based on whitelisted IPs.
    """

    # List of allowed IP addresses
    ALLOWED_IPS = ['127.0.0.1', '24.184.47.80','75.223.174.33', '108.54.16.186', '75.225.110.112', '97.133.52.183' ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request IP is allowed
        if request.META['REMOTE_ADDR'] not in self.ALLOWED_IPS:
            return HttpResponseForbidden("Access Denied")

        response = self.get_response(request)
        return response
