# employees/views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from core.models import EmployeeProfile
from core.serializers import EmployeeProfileSerializer
from .models import LeaveRequest
from .serializers import LeaveRequestSerializer


class EmployeeProfileViewSet(viewsets.ModelViewSet):  # Changed from ReadOnlyModelViewSet
    """
    API for managing employee profiles.
    - HR Manager: Full CRUD access
    - Other users: Read-only access
    """
    queryset = EmployeeProfile.objects.filter(is_active=True).select_related(
        'user', 'department'
    )
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    
    filterset_fields = {
        'position': ['exact', 'in'],
        'department__name': ['exact', 'icontains'],
        'is_active': ['exact'],
    }
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'position'
    ]
    ordering_fields = ['user__first_name', 'position', 'date_joined']
    ordering = ['user__first_name']


class LeaveRequestViewSet(viewsets.ModelViewSet):
    """
    API for leave requests.
    - Staff: Create & view own requests
    - HR Manager / Supervisor: View all, approve/reject
    - Department Manager: View their team's requests
    """
    queryset = LeaveRequest.objects.all().select_related(
        'employee__user', 'employee__department', 'reviewed_by__user'
    )
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = {
        'status': ['exact', 'in'],
        'employee__department__name': ['exact', 'icontains'],
        'employee__position': ['exact'],
        'start_date': ['exact', 'gte', 'lte'],
        'end_date': ['exact', 'gte', 'lte'],
    }
    search_fields = [
        'employee__user__first_name',
        'employee__user__last_name',
        'employee__user__email',
        'reason'
    ]
    ordering_fields = ['requested_at', 'start_date', 'status']
    ordering = ['-requested_at']

    def get_queryset(self):
        user_profile = self.request.user.profile

        if user_profile.position in ['HR Manager', 'Human Resources / R&D Manager']:
            # HR sees all
            return self.queryset

        if user_profile.position in ['CEO', 'EDBO']:
            # Executive sees all
            return self.queryset

        if 'Manager' in user_profile.position:
            # Department managers see their team's requests
            return self.queryset.filter(employee__department=user_profile.department)

        # Regular staff: only their own requests
        return self.queryset.filter(employee=user_profile)

    def perform_create(self, serializer):
        # Set status to pending when creating
        serializer.save(status='pending')

    def perform_update(self, serializer):
        # Only HR or managers can approve/reject
        if 'status' in serializer.validated_data:
            new_status = serializer.validated_data['status']
            if new_status != 'pending':
                user_position = self.request.user.profile.position
                
                # Check if user has permission to approve/reject
                if user_position not in ['HR Manager', 'CEO', 'EDBO'] and \
                   'Manager' not in user_position:
                    raise ValidationError("You do not have permission to approve/reject leaves.")

                serializer.save(
                    reviewed_by=self.request.user.profile,
                    reviewed_at=timezone.now()
                )
                return
        super().perform_update(serializer)