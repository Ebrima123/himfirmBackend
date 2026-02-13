# projects/views.py
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import (
    Q, Count, Sum, Avg, F, Case, When, Value, 
    IntegerField, DecimalField, Prefetch
)
from django.utils import timezone
from datetime import timedelta

from .models import (
    LandParcel, ProjectType, Project, ProjectTeamMember,
    ProjectPhase, ProjectMilestone, TaskCategory, ProjectTask,
    TaskDependency, ResourceCategory, ProjectResource,
    ProjectResourceAllocation, BudgetCategory, ProjectBudgetLine,
    ProjectExpense, PermitType, ProjectPermit, InspectionType,
    ProjectInspection, ProjectRisk, ProjectIssue, ChangeOrder,
    DailyProgressReport, ProjectMeeting, SafetyIncident
)

from .serializers import (
    LandParcelSerializer, LandParcelListSerializer,
    ProjectTypeSerializer, ProjectSerializer, ProjectListSerializer,
    ProjectTeamMemberSerializer, ProjectPhaseSerializer,
    ProjectMilestoneSerializer, TaskCategorySerializer,
    ProjectTaskSerializer, ProjectTaskListSerializer,
    TaskDependencySerializer, ResourceCategorySerializer,
    ProjectResourceSerializer, ProjectResourceAllocationSerializer,
    BudgetCategorySerializer, ProjectBudgetLineSerializer,
    ProjectExpenseSerializer, PermitTypeSerializer,
    ProjectPermitSerializer, InspectionTypeSerializer,
    ProjectInspectionSerializer, ProjectRiskSerializer,
    ProjectIssueSerializer, ChangeOrderSerializer,
    DailyProgressReportSerializer, ProjectMeetingSerializer,
    SafetyIncidentSerializer, ProjectDashboardSerializer
)

from .filters import (
    LandParcelFilter, ProjectFilter, ProjectTaskFilter,
    ProjectExpenseFilter, ProjectPermitFilter
)


# ==================== LAND & PROPERTY ====================

class LandParcelViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing land parcels (acquisition & development bank).
    Accessible to PMDC Manager, Project Supervisors, CEO/EDBO.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LandParcelFilter
    search_fields = [
        'title_number', 'plot_number', 'location', 'address',
        'city', 'state_province', 'legal_description'
    ]
    ordering_fields = [
        'acquisition_date', 'size_sq_meters', 'acquisition_cost',
        'current_market_value', 'created_at'
    ]
    ordering = ['-acquisition_date']

    def get_queryset(self):
        queryset = LandParcel.objects.all()
        
        # Add status filter shortcuts
        status_filter = self.request.query_params.get('quick_filter', None)
        if status_filter == 'available':
            queryset = queryset.filter(status='available')
        elif status_filter == 'in_development':
            queryset = queryset.filter(status='in_development')
        
        return queryset.order_by('-acquisition_date')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return LandParcelListSerializer
        return LandParcelSerializer
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get land parcel statistics"""
        queryset = self.filter_queryset(self.get_queryset())
        
        stats = queryset.aggregate(
            total_parcels=Count('id'),
            total_area=Sum('size_sq_meters'),
            total_acquisition_cost=Sum('acquisition_cost'),
            total_market_value=Sum('current_market_value'),
            avg_size=Avg('size_sq_meters'),
        )
        
        stats['by_status'] = dict(
            queryset.values('status').annotate(
                count=Count('id')
            ).values_list('status', 'count')
        )
        
        stats['by_zoning'] = dict(
            queryset.values('zoning').annotate(
                count=Count('id')
            ).values_list('zoning', 'count')
        )
        
        stats['appreciation'] = float(
            (stats['total_market_value'] or 0) - (stats['total_acquisition_cost'] or 0)
        )
        
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def projects(self, request, pk=None):
        """Get all projects on this land parcel"""
        parcel = self.get_object()
        projects = Project.objects.filter(land_parcel=parcel)
        serializer = ProjectListSerializer(projects, many=True)
        return Response(serializer.data)


# ==================== PROJECT CORE ====================

class ProjectTypeViewSet(viewsets.ModelViewSet):
    """API endpoint for project types"""
    queryset = ProjectType.objects.filter(is_active=True).order_by('name')
    serializer_class = ProjectTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code']


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for real estate development projects.
    Core module for PMDC Manager and PPD Unit.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectFilter
    search_fields = [
        'name', 'code', 'description', 'land_parcel__title_number',
        'land_parcel__location', 'client_name'
    ]
    ordering_fields = [
        'start_date', 'expected_completion', 'budget',
        'actual_cost', 'progress_percentage', 'created_at'
    ]
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Project.objects.select_related(
            'land_parcel', 'manager', 'project_type',
            'architect', 'engineer', 'site_supervisor'
        ).prefetch_related(
            'team_members',
            Prefetch('tasks', queryset=ProjectTask.objects.select_related('assigned_to'))
        )
        
        # Annotate with computed fields
        queryset = queryset.annotate(
            task_count=Count('tasks', distinct=True),
            completed_tasks=Count(
                'tasks',
                filter=Q(tasks__status='completed'),
                distinct=True
            ),
            overdue_tasks=Count(
                'tasks',
                filter=Q(
                    tasks__status__in=['pending', 'in_progress'],
                    tasks__due_date__lt=timezone.now().date()
                ),
                distinct=True
            ),
            budget_variance=F('budget') - F('actual_cost'),
            is_delayed=Case(
                When(
                    Q(expected_completion__lt=timezone.now().date()) &
                    ~Q(status__in=['completed', 'cancelled']),
                    then=Value(True)
                ),
                default=Value(False),
                output_field=IntegerField()
            )
        )
        
        # Quick filters
        quick_filter = self.request.query_params.get('quick_filter', None)
        if quick_filter == 'active':
            queryset = queryset.exclude(status__in=['completed', 'cancelled'])
        elif quick_filter == 'delayed':
            queryset = queryset.filter(
                expected_completion__lt=timezone.now().date()
            ).exclude(status__in=['completed', 'cancelled'])
        elif quick_filter == 'my_projects':
            user = self.request.user
            queryset = queryset.filter(
                Q(manager=user.profile) |
                Q(team_members=user.profile)
            ).distinct()
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectSerializer
    
    def perform_create(self, serializer):
        # Auto-assign current user as manager if not specified
        if not serializer.validated_data.get('manager'):
            profile = self.request.user.profile
            if hasattr(profile, 'position') and profile.position in [
                'PMDC Manager', 'Project Supervisor', 'Project Manager'
            ]:
                serializer.save(manager=profile)
            else:
                serializer.save()
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get project dashboard statistics"""
        queryset = self.filter_queryset(self.get_queryset())
        today = timezone.now().date()
        
        stats = {
            'total_projects': queryset.count(),
            'active_projects': queryset.exclude(
                status__in=['completed', 'cancelled']
            ).count(),
            'completed_projects': queryset.filter(status='completed').count(),
            'delayed_projects': queryset.filter(
                expected_completion__lt=today
            ).exclude(status__in=['completed', 'cancelled']).count(),
            
            'total_budget': queryset.aggregate(
                total=Sum('budget')
            )['total'] or 0,
            'total_spent': queryset.aggregate(
                total=Sum('actual_cost')
            )['total'] or 0,
            'budget_variance': queryset.aggregate(
                variance=Sum(F('budget') - F('actual_cost'))
            )['variance'] or 0,
            
            'total_tasks': ProjectTask.objects.filter(
                project__in=queryset
            ).count(),
            'completed_tasks': ProjectTask.objects.filter(
                project__in=queryset,
                status='completed'
            ).count(),
            'overdue_tasks': ProjectTask.objects.filter(
                project__in=queryset,
                status__in=['pending', 'in_progress'],
                due_date__lt=today
            ).count(),
            
            'active_risks': ProjectRisk.objects.filter(
                project__in=queryset,
                status__in=['identified', 'analyzing', 'mitigating']
            ).count(),
            'open_issues': ProjectIssue.objects.filter(
                project__in=queryset,
                status__in=['open', 'in_progress']
            ).count(),
            'pending_change_orders': ChangeOrder.objects.filter(
                project__in=queryset,
                status__in=['draft', 'submitted', 'under_review']
            ).count(),
            
            'projects_by_status': dict(
                queryset.values('status').annotate(
                    count=Count('id')
                ).values_list('status', 'count')
            ),
            'projects_by_priority': dict(
                queryset.values('priority').annotate(
                    count=Count('id')
                ).values_list('priority', 'count')
            ),
        }
        
        serializer = ProjectDashboardSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get project timeline with phases and milestones"""
        project = self.get_object()
        
        phases = ProjectPhaseSerializer(
            project.phases.all().order_by('sequence'),
            many=True
        ).data
        
        milestones = ProjectMilestoneSerializer(
            project.milestones.all().order_by('target_date'),
            many=True
        ).data
        
        return Response({
            'phases': phases,
            'milestones': milestones
        })
    
    @action(detail=True, methods=['get'])
    def financial_summary(self, request, pk=None):
        """Get detailed financial summary"""
        project = self.get_object()
        
        budget_lines = project.budget_lines.aggregate(
            total_budgeted=Sum('budgeted_amount'),
            total_actual=Sum('actual_amount'),
            total_committed=Sum('committed_amount')
        )
        
        expenses_by_type = dict(
            project.expenses.values('expense_type').annotate(
                total=Sum('amount')
            ).values_list('expense_type', 'total')
        )
        
        expenses_by_category = dict(
            project.expenses.values('category__name').annotate(
                total=Sum('amount')
            ).values_list('category__name', 'total')
        )
        
        return Response({
            'project_budget': float(project.budget),
            'contingency_budget': float(project.contingency_budget),
            'actual_cost': float(project.actual_cost),
            'variance': float(project.budget - project.actual_cost),
            'budget_lines': budget_lines,
            'expenses_by_type': expenses_by_type,
            'expenses_by_category': expenses_by_category,
            'budget_utilization': (
                float(project.actual_cost) / float(project.budget) * 100
            ) if project.budget > 0 else 0
        })
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update project progress percentage"""
        project = self.get_object()
        progress = request.data.get('progress_percentage')
        
        if progress is not None:
            try:
                progress = float(progress)
                if 0 <= progress <= 100:
                    project.progress_percentage = progress
                    project.save()
                    return Response({'status': 'progress updated'})
                else:
                    return Response(
                        {'error': 'Progress must be between 0 and 100'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except ValueError:
                return Response(
                    {'error': 'Invalid progress value'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {'error': 'progress_percentage required'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ProjectTeamMemberViewSet(viewsets.ModelViewSet):
    """API endpoint for project team members"""
    queryset = ProjectTeamMember.objects.select_related(
        'project', 'employee', 'employee__user'
    ).filter(is_active=True).order_by('project', 'role')
    serializer_class = ProjectTeamMemberSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['project', 'employee', 'role', 'is_active']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'role']


# ==================== PHASES & MILESTONES ====================

class ProjectPhaseViewSet(viewsets.ModelViewSet):
    """API endpoint for project phases"""
    queryset = ProjectPhase.objects.select_related('project').order_by('project', 'sequence')
    serializer_class = ProjectPhaseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['sequence', 'start_date', 'end_date']
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update phase progress"""
        phase = self.get_object()
        progress = request.data.get('progress_percentage')
        
        if progress is not None:
            try:
                progress = float(progress)
                if 0 <= progress <= 100:
                    phase.progress_percentage = progress
                    if progress == 100:
                        phase.status = 'completed'
                        phase.actual_end_date = timezone.now().date()
                    elif progress > 0:
                        phase.status = 'in_progress'
                        if not phase.actual_start_date:
                            phase.actual_start_date = timezone.now().date()
                    phase.save()
                    return Response({'status': 'progress updated'})
            except ValueError:
                pass
        
        return Response(
            {'error': 'Invalid progress value'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ProjectMilestoneViewSet(viewsets.ModelViewSet):
    """API endpoint for project milestones"""
    queryset = ProjectMilestone.objects.select_related(
        'project', 'phase', 'responsible_person'
    ).order_by('target_date')
    serializer_class = ProjectMilestoneSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'phase', 'status', 'is_critical']
    search_fields = ['name', 'description']
    ordering_fields = ['target_date', 'actual_date']
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming milestones"""
        days = int(request.query_params.get('days', 30))
        queryset = self.filter_queryset(self.get_queryset())
        
        upcoming = queryset.filter(
            status='pending',
            target_date__lte=timezone.now().date() + timedelta(days=days)
        ).order_by('target_date')
        
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)


# ==================== TASKS ====================

class TaskCategoryViewSet(viewsets.ModelViewSet):
    """API endpoint for task categories"""
    queryset = TaskCategory.objects.filter(is_active=True).order_by('name')
    serializer_class = TaskCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class ProjectTaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tasks within projects.
    Used by Project Supervisors and assigned team members.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectTaskFilter
    search_fields = [
        'title', 'description', 'task_code',
        'project__name', 'project__code'
    ]
    ordering_fields = [
        'due_date', 'start_date', 'priority',
        'progress_percentage', 'created_at'
    ]
    ordering = ['due_date']

    def get_queryset(self):
        queryset = ProjectTask.objects.select_related(
            'project', 'phase', 'category', 'assigned_to',
            'created_by', 'approved_by', 'parent_task'
        ).prefetch_related('subtasks', 'dependencies')
        
        # Annotate with is_overdue
        queryset = queryset.annotate(
            is_overdue=Case(
                When(
                    Q(status__in=['pending', 'in_progress']) &
                    Q(due_date__lt=timezone.now().date()),
                    then=Value(True)
                ),
                default=Value(False),
                output_field=IntegerField()
            )
        )
        
        # Role-based filtering
        user = self.request.user
        view_param = self.request.query_params.get('view', None)
        
        if view_param == 'my_tasks':
            queryset = queryset.filter(assigned_to=user.profile)
        elif view_param == 'created_by_me':
            queryset = queryset.filter(created_by=user.profile)
        elif hasattr(user, 'profile'):
            # If not admin/manager, show only assigned tasks
            if not hasattr(user.profile, 'position') or user.profile.position not in [
                'PMDC Manager', 'Project Supervisor', 'Project Manager', 'CEO', 'EDBO'
            ]:
                queryset = queryset.filter(assigned_to=user.profile)
        
        # Quick filters
        quick_filter = self.request.query_params.get('quick_filter', None)
        if quick_filter == 'overdue':
            queryset = queryset.filter(
                status__in=['pending', 'in_progress'],
                due_date__lt=timezone.now().date()
            )
        elif quick_filter == 'due_soon':
            queryset = queryset.filter(
                status__in=['pending', 'in_progress'],
                due_date__lte=timezone.now().date() + timedelta(days=7)
            )
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectTaskListSerializer
        return ProjectTaskSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.profile)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark task as completed"""
        task = self.get_object()
        task.status = 'completed'
        task.progress_percentage = 100
        task.completed_date = timezone.now().date()
        task.save()
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a task"""
        task = self.get_object()
        if task.requires_approval:
            task.is_approved = True
            task.approved_by = request.user.profile
            task.approval_date = timezone.now()
            task.save()
            return Response({'status': 'task approved'})
        return Response(
            {'error': 'Task does not require approval'},
            status=status.HTTP_400_BAD_REQUEST
        )


class TaskDependencyViewSet(viewsets.ModelViewSet):
    """API endpoint for task dependencies"""
    queryset = TaskDependency.objects.select_related('task', 'depends_on').all()
    serializer_class = TaskDependencySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['task', 'depends_on', 'dependency_type']


# ==================== RESOURCES ====================

class ResourceCategoryViewSet(viewsets.ModelViewSet):
    """API endpoint for resource categories"""
    queryset = ResourceCategory.objects.filter(is_active=True).order_by('name')
    serializer_class = ResourceCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class ProjectResourceViewSet(viewsets.ModelViewSet):
    """API endpoint for project resources"""
    queryset = ProjectResource.objects.select_related('category').filter(
        is_active=True
    ).order_by('name')
    serializer_class = ProjectResourceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['resource_type', 'category', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'unit_cost', 'quantity_available']
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get resources below minimum quantity"""
        queryset = self.filter_queryset(self.get_queryset())
        low_stock = queryset.filter(quantity_available__lte=F('minimum_quantity'))
        serializer = self.get_serializer(low_stock, many=True)
        return Response(serializer.data)


class ProjectResourceAllocationViewSet(viewsets.ModelViewSet):
    """API endpoint for resource allocations"""
    queryset = ProjectResourceAllocation.objects.select_related(
        'project', 'resource', 'task', 'allocated_by'
    ).order_by('-allocation_date')
    serializer_class = ProjectResourceAllocationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'resource', 'task']
    search_fields = ['resource__name', 'project__name']
    ordering_fields = ['allocation_date', 'expected_return_date']
    
    def perform_create(self, serializer):
        serializer.save(allocated_by=self.request.user.profile)


# ==================== BUDGET & COSTS ====================

class BudgetCategoryViewSet(viewsets.ModelViewSet):
    """API endpoint for budget categories"""
    queryset = BudgetCategory.objects.filter(is_active=True).order_by('code')
    serializer_class = BudgetCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code', 'description']


class ProjectBudgetLineViewSet(viewsets.ModelViewSet):
    """API endpoint for project budget lines"""
    queryset = ProjectBudgetLine.objects.select_related(
        'project', 'category', 'phase'
    ).order_by('project', 'category')
    serializer_class = ProjectBudgetLineSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['project', 'category', 'phase']
    search_fields = ['description']


class ProjectExpenseViewSet(viewsets.ModelViewSet):
    """API endpoint for project expenses"""
    queryset = ProjectExpense.objects.select_related(
        'project', 'budget_line', 'category', 'approved_by', 'submitted_by'
    ).order_by('-expense_date')
    serializer_class = ProjectExpenseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectExpenseFilter
    search_fields = [
        'description', 'invoice_number', 'vendor_name',
        'project__name', 'project__code'
    ]
    ordering_fields = ['expense_date', 'amount', 'payment_status']
    
    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user.profile)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an expense"""
        expense = self.get_object()
        expense.payment_status = 'approved'
        expense.approved_by = request.user.profile
        expense.approval_date = timezone.now()
        expense.save()
        
        serializer = self.get_serializer(expense)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark expense as paid"""
        expense = self.get_object()
        if expense.payment_status == 'approved':
            expense.payment_status = 'paid'
            expense.save()
            return Response({'status': 'marked as paid'})
        return Response(
            {'error': 'Expense must be approved first'},
            status=status.HTTP_400_BAD_REQUEST
        )


# ==================== PERMITS & APPROVALS ====================

class PermitTypeViewSet(viewsets.ModelViewSet):
    """API endpoint for permit types"""
    queryset = PermitType.objects.filter(is_active=True).order_by('name')
    serializer_class = PermitTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description', 'issuing_authority']


class ProjectPermitViewSet(viewsets.ModelViewSet):
    """API endpoint for project permits"""
    queryset = ProjectPermit.objects.select_related(
        'project', 'permit_type', 'responsible_person'
    ).order_by('-application_date')
    serializer_class = ProjectPermitSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectPermitFilter
    search_fields = [
        'permit_number', 'issuing_authority',
        'project__name', 'project__code'
    ]
    ordering_fields = ['application_date', 'approval_date', 'expiry_date']
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get permits expiring in next 30 days"""
        days = int(request.query_params.get('days', 30))
        queryset = self.filter_queryset(self.get_queryset())
        
        expiring = queryset.filter(
            status='approved',
            expiry_date__lte=timezone.now().date() + timedelta(days=days)
        ).order_by('expiry_date')
        
        serializer = self.get_serializer(expiring, many=True)
        return Response(serializer.data)


# ==================== QUALITY & INSPECTIONS ====================

class InspectionTypeViewSet(viewsets.ModelViewSet):
    """API endpoint for inspection types"""
    queryset = InspectionType.objects.filter(is_active=True).order_by('name')
    serializer_class = InspectionTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class ProjectInspectionViewSet(viewsets.ModelViewSet):
    """API endpoint for project inspections"""
    queryset = ProjectInspection.objects.select_related(
        'project', 'inspection_type', 'phase', 'conducted_by'
    ).order_by('-inspection_date')
    serializer_class = ProjectInspectionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'inspection_type', 'status', 'phase']
    search_fields = ['inspector_name', 'findings', 'project__name']
    ordering_fields = ['inspection_date', 'follow_up_date']
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming inspections"""
        queryset = self.filter_queryset(self.get_queryset())
        upcoming = queryset.filter(
            status='scheduled',
            inspection_date__gte=timezone.now().date()
        ).order_by('inspection_date')
        
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)


# ==================== RISKS & ISSUES ====================

class ProjectRiskViewSet(viewsets.ModelViewSet):
    """API endpoint for project risks"""
    queryset = ProjectRisk.objects.select_related(
        'project', 'identified_by', 'owner'
    ).order_by('-identified_date')
    serializer_class = ProjectRiskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'status', 'probability', 'impact']
    search_fields = ['title', 'description', 'category']
    ordering_fields = ['identified_date', 'review_date']
    
    @action(detail=False, methods=['get'])
    def high_priority(self, request):
        """Get high priority risks"""
        queryset = self.filter_queryset(self.get_queryset())
        high_risks = queryset.filter(
            status__in=['identified', 'analyzing', 'mitigating'],
            probability__in=['high', 'very_high'],
            impact__in=['major', 'critical']
        )
        
        serializer = self.get_serializer(high_risks, many=True)
        return Response(serializer.data)


class ProjectIssueViewSet(viewsets.ModelViewSet):
    """API endpoint for project issues"""
    queryset = ProjectIssue.objects.select_related(
        'project', 'related_task', 'reported_by', 'assigned_to'
    ).order_by('-reported_date')
    serializer_class = ProjectIssueSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'status', 'severity', 'assigned_to']
    search_fields = ['title', 'description']
    ordering_fields = ['reported_date', 'resolved_date', 'severity']
    
    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user.profile)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark issue as resolved"""
        issue = self.get_object()
        resolution = request.data.get('resolution', '')
        
        issue.status = 'resolved'
        issue.resolved_date = timezone.now()
        issue.resolution = resolution
        issue.save()
        
        serializer = self.get_serializer(issue)
        return Response(serializer.data)


# ==================== CHANGE ORDERS ====================

class ChangeOrderViewSet(viewsets.ModelViewSet):
    """API endpoint for change orders"""
    queryset = ChangeOrder.objects.select_related(
        'project', 'requested_by', 'approved_by'
    ).order_by('-created_at')
    serializer_class = ChangeOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'status']
    search_fields = ['change_order_number', 'title', 'description']
    ordering_fields = ['submitted_date', 'approved_date', 'cost_impact']
    
    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user.profile)
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit change order for review"""
        change_order = self.get_object()
        if change_order.status == 'draft':
            change_order.status = 'submitted'
            change_order.submitted_date = timezone.now().date()
            change_order.save()
            return Response({'status': 'submitted'})
        return Response(
            {'error': 'Can only submit draft change orders'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve change order"""
        change_order = self.get_object()
        if change_order.status in ['submitted', 'under_review']:
            change_order.status = 'approved'
            change_order.approved_date = timezone.now().date()
            change_order.approved_by = request.user.profile
            change_order.save()
            
            # Update project budget and timeline
            project = change_order.project
            project.budget += change_order.cost_impact
            if change_order.schedule_impact_days > 0:
                project.expected_completion += timedelta(
                    days=change_order.schedule_impact_days
                )
            project.save()
            
            return Response({'status': 'approved'})
        return Response(
            {'error': 'Invalid status for approval'},
            status=status.HTTP_400_BAD_REQUEST
        )


# ==================== DAILY REPORTS ====================

class DailyProgressReportViewSet(viewsets.ModelViewSet):
    """API endpoint for daily progress reports"""
    queryset = DailyProgressReport.objects.select_related(
        'project', 'submitted_by'
    ).order_by('-report_date')
    serializer_class = DailyProgressReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'report_date', 'weather_condition']
    search_fields = ['work_performed', 'project__name']
    ordering_fields = ['report_date']
    
    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user.profile)


# ==================== MEETINGS ====================

class ProjectMeetingViewSet(viewsets.ModelViewSet):
    """API endpoint for project meetings"""
    queryset = ProjectMeeting.objects.select_related(
        'project', 'organizer'
    ).prefetch_related('attendees').order_by('-meeting_date')
    serializer_class = ProjectMeetingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'meeting_type', 'organizer']
    search_fields = ['title', 'agenda', 'minutes']
    ordering_fields = ['meeting_date', 'duration_minutes']
    
    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user.profile)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming meetings"""
        queryset = self.filter_queryset(self.get_queryset())
        upcoming = queryset.filter(
            meeting_date__gte=timezone.now()
        ).order_by('meeting_date')
        
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)


# ==================== SAFETY ====================

class SafetyIncidentViewSet(viewsets.ModelViewSet):
    """API endpoint for safety incidents"""
    queryset = SafetyIncident.objects.select_related(
        'project', 'reported_by', 'investigated_by'
    ).order_by('-incident_date')
    serializer_class = SafetyIncidentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'severity', 'authorities_notified']
    search_fields = ['description', 'location', 'persons_involved']
    ordering_fields = ['incident_date', 'severity']
    
    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user.profile)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get safety statistics"""
        queryset = self.filter_queryset(self.get_queryset())
        
        stats = {
            'total_incidents': queryset.count(),
            'by_severity': dict(
                queryset.values('severity').annotate(
                    count=Count('id')
                ).values_list('severity', 'count')
            ),
            'by_project': dict(
                queryset.values('project__name').annotate(
                    count=Count('id')
                ).values_list('project__name', 'count')
            ),
            'days_since_last_incident': None
        }
        
        last_incident = queryset.first()
        if last_incident:
            delta = timezone.now() - last_incident.incident_date
            stats['days_since_last_incident'] = delta.days
        
        return Response(stats)