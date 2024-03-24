# views.py
from django.db.models import F
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import UserProfile  # Assuming you have a UserProfile model


class ExternalView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            user_demo_data = UserProfile.objects.filter(user=request.user).annotate(
                sexuality_name=F('identity_sexuality__name'),
                gender_name=F('identity_gender__name'),
                ethic_name=F('identity_ethic__name'),
                pronouns_name=F('identity_pronouns__name'),
            ).values(
                'sexuality_name',
                'gender_name',
                'ethic_name',
                'pronouns_name',
                "disability",
                "care_giver",
                "veteran_status",
            )

            if not user_demo_data:
                print(f"No UserProfile found for user {request.user.id}")
                return Response(
                    {"error": "UserProfile data not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            user_account_data = {
                "is_company_review_access_active": request.user.is_company_review_access_active,
                "company_review_tokens": request.user.company_review_tokens,
            }
            user_data = {
                "user_demo": list(user_demo_data),
                "user_account": user_account_data,
            }
            return Response(user_data, status=status.HTTP_200_OK)

        except UserProfile.DoesNotExist:
            print(f"UserProfile does not exist for user {request.user.id}")
            return Response(
                {"error": "UserProfile not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"Unexpected error retrieving user data for {request.user.id}: {e}")
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
