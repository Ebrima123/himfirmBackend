# core/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import EmployeeProfileSerializer

# core/views.py (update LoginView)
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')        # Changed from 'username'
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)  # authenticate uses email
        if user:
            refresh = RefreshToken.for_user(user)
            profile = user.profile
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.get_full_name(),
                    'role': profile.position,
                    'department': profile.department.name if profile.department else None,
                },
                'mfa_required': user.is_mfa_enabled
            })
        return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
class ProfileView(APIView):
    def get(self, request):
        serializer = EmployeeProfileSerializer(request.user.profile)
        return Response(serializer.data)