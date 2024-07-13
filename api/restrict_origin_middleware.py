from django.http import JsonResponse


class RestrictOriginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_origins = [
            "https://www.beta.techbychoice.org",
            "https://beta.techbychoice.org",
            "https://beta.api.dev.techbychoice.org",
            "https://www.beta.api.dev.techbychoice.org",
            "https://www.opendoors.api.techbychoice.org",
            "https://opendoors.api.techbychoice.org",

        ]

    def __call__(self, request):
        origin = request.headers.get('Origin')
        if origin and origin not in self.allowed_origins:
            return JsonResponse({'error': 'Origin not allowed'}, status=403)
        response = self.get_response(request)
        return response
