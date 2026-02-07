# core/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets  # Added viewsets here
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import Department
from .serializers import EmployeeProfileSerializer, DepartmentSerializer


# Your LoginView (keep as is)
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)
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


# Your ProfileView (with the fix)
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's profile"""
        serializer = EmployeeProfileSerializer(request.user.profile)
        return Response(serializer.data)
    
    def patch(self, request):
        """Update current user's profile (partial update)"""
        serializer = EmployeeProfileSerializer(
            request.user.profile, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        """Update current user's profile (full update)"""
        serializer = EmployeeProfileSerializer(
            request.user.profile, 
            data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Department ViewSet
class DepartmentViewSet(viewsets.ModelViewSet):
    """
    API for managing departments.
    - All authenticated users can view departments
    - Only HR Manager can create/update/delete
    """
    queryset = Department.objects.all().order_by('name')
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]