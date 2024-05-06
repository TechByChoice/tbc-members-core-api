from knox.models import AuthToken
from rest_framework import permissions, views, response


class UserPermissionAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        permissions = request.user.is_authenticated
        return response.Response({'permissions': permissions})
