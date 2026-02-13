# projects/serializers.py
from rest_framework import serializers
from django.db.models import Sum, Count, Q
from .models import (
    LandParcel, ProjectType, Project, ProjectTeamMember,
    ProjectPhase, ProjectMilestone, TaskCategory, ProjectTask,
    TaskDependency, ResourceCategory, ProjectResource,
    ProjectResourceAllocation, BudgetCategory, ProjectBudgetLine,
    ProjectExpense, PermitType, ProjectPermit, InspectionType,
    ProjectInspection, ProjectRisk, ProjectIssue, ChangeOrder,
    DailyProgressReport, ProjectMeeting, SafetyIncident
)
from documents.serializers import DocumentSerializer
from core.serializers import EmployeeProfileSerializer


# ==================== LAND & PROPERTY ====================

class LandParcelListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for lists"""
    class Meta:
        model = LandParcel
        fields = [
            'id', 'title_number', 'plot_number', 'location', 'city',
            'size_sq_meters', 'status', 'acquisition_cost', 'zoning'
        ]


class LandParcelSerializer(serializers.ModelSerializer):
    """Full serializer with all details"""
    documents = DocumentSerializer(many=True, read_only=True)
    current_value = serializers.DecimalField(
        source='current_market_value',
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    appreciation = serializers.SerializerMethodField()
    
    class Meta:
        model = LandParcel
        fields = '__all__'
    
    def get_appreciation(self, obj):
        if obj.current_market_value and obj.acquisition_cost:
            return float(obj.current_market_value - obj.acquisition_cost)
        return None


# ==================== PROJECT CORE ====================

class ProjectTypeSerializer(serializers.ModelSerializer):
    project_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectType
        fields = '__all__'
    
    def get_project_count(self, obj):
        return obj.project_set.count()


class ProjectTeamMemberSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.user.email', read_only=True)
    employee_position = serializers.CharField(source='employee.position', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = ProjectTeamMember
        fields = '__all__'


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for project lists"""
    manager_name = serializers.CharField(source='manager.user.get_full_name', read_only=True)
    land_parcel_location = serializers.CharField(source='land_parcel.location', read_only=True)
    project_type_name = serializers.CharField(source='project_type.name', read_only=True)
    
    # Computed fields
    task_count = serializers.IntegerField(read_only=True)
    completed_tasks = serializers.IntegerField(read_only=True)
    overdue_tasks = serializers.IntegerField(read_only=True)
    budget_variance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    days_until_completion = serializers.SerializerMethodField()
    is_delayed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'code', 'name', 'project_type', 'project_type_name',
            'status', 'priority', 'progress_percentage',
            'manager', 'manager_name', 'land_parcel', 'land_parcel_location',
            'start_date', 'expected_completion', 'actual_completion',
            'budget', 'actual_cost', 'budget_variance',
            'task_count', 'completed_tasks', 'overdue_tasks',
            'is_delayed', 'days_until_completion', 'created_at'
        ]
    
    def get_days_until_completion(self, obj):
        if obj.expected_completion and obj.status not in ['completed', 'cancelled']:
            from django.utils import timezone
            delta = obj.expected_completion - timezone.now().date()
            return delta.days
        return None


class ProjectSerializer(serializers.ModelSerializer):
    """Full project serializer with all details"""
    # Related object details
    land_parcel_details = LandParcelListSerializer(source='land_parcel', read_only=True)
    project_type_name = serializers.CharField(source='project_type.name', read_only=True)
    manager_details = EmployeeProfileSerializer(source='manager', read_only=True)
    architect_name = serializers.CharField(source='architect.user.get_full_name', read_only=True)
    engineer_name = serializers.CharField(source='engineer.user.get_full_name', read_only=True)
    site_supervisor_name = serializers.CharField(source='site_supervisor.user.get_full_name', read_only=True)
    
    # Documents
    documents = DocumentSerializer(many=True, read_only=True)
    
    # Team
    team_member_details = ProjectTeamMemberSerializer(
        source='projectteammember_set',
        many=True,
        read_only=True
    )
    
    # Statistics
    task_statistics = serializers.SerializerMethodField()
    budget_statistics = serializers.SerializerMethodField()
    phase_statistics = serializers.SerializerMethodField()
    timeline_info = serializers.SerializerMethodField()
    
    # Computed properties
    budget_variance = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    is_delayed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Project
        fields = '__all__'
    
    def get_task_statistics(self, obj):
        tasks = obj.tasks.all()
        total = tasks.count()
        
        return {
            'total': total,
            'pending': tasks.filter(status='pending').count(),
            'in_progress': tasks.filter(status='in_progress').count(),
            'completed': tasks.filter(status='completed').count(),
            'overdue': tasks.filter(
                status__in=['pending', 'in_progress'],
                due_date__lt=serializers.DateField().to_representation(
                    serializers.DateField().to_internal_value(
                        serializers.DateField().get_default()
                    )
                )
            ).count() if total > 0 else 0,
            'completion_rate': (tasks.filter(status='completed').count() / total * 100) if total > 0 else 0
        }
    
    def get_budget_statistics(self, obj):
        budget_lines = obj.budget_lines.aggregate(
            total_budgeted=Sum('budgeted_amount'),
            total_actual=Sum('actual_amount'),
            total_committed=Sum('committed_amount')
        )
        
        expenses = obj.expenses.aggregate(
            total_expenses=Sum('amount'),
            paid_expenses=Sum('amount', filter=Q(payment_status='paid')),
            pending_expenses=Sum('amount', filter=Q(payment_status='pending'))
        )
        
        return {
            'total_budget': float(obj.budget),
            'contingency_budget': float(obj.contingency_budget),
            'actual_cost': float(obj.actual_cost),
            'variance': float(obj.budget_variance),
            'budget_lines': budget_lines,
            'expenses': expenses,
            'utilization_percentage': (float(obj.actual_cost) / float(obj.budget) * 100) if obj.budget > 0 else 0
        }
    
    def get_phase_statistics(self, obj):
        phases = obj.phases.all()
        return {
            'total_phases': phases.count(),
            'completed_phases': phases.filter(status='completed').count(),
            'current_phase': phases.filter(status='in_progress').first().name if phases.filter(status='in_progress').exists() else None
        }
    
    def get_timeline_info(self, obj):
        from django.utils import timezone
        today = timezone.now().date()
        
        duration = None
        elapsed = None
        remaining = None
        
        if obj.start_date and obj.expected_completion:
            duration = (obj.expected_completion - obj.start_date).days
            elapsed = (today - obj.start_date).days if today >= obj.start_date else 0
            remaining = (obj.expected_completion - today).days if today <= obj.expected_completion else 0
        
        return {
            'duration_days': duration,
            'elapsed_days': elapsed,
            'remaining_days': remaining,
            'is_delayed': obj.is_delayed,
            'delay_days': (today - obj.expected_completion).days if obj.is_delayed else 0
        }


# ==================== PHASES & MILESTONES ====================

class ProjectPhaseSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    task_count = serializers.IntegerField(source='tasks.count', read_only=True)
    milestone_count = serializers.IntegerField(source='milestones.count', read_only=True)
    variance = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectPhase
        fields = '__all__'
    
    def get_variance(self, obj):
        return float(obj.budgeted_amount - obj.actual_cost) if obj.budgeted_amount else None


class ProjectMilestoneSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    phase_name = serializers.CharField(source='phase.name', read_only=True)
    responsible_person_name = serializers.CharField(
        source='responsible_person.user.get_full_name',
        read_only=True
    )
    documents = DocumentSerializer(many=True, read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectMilestone
        fields = '__all__'
    
    def get_is_overdue(self, obj):
        if obj.status == 'pending':
            from django.utils import timezone
            return timezone.now().date() > obj.target_date
        return False


# ==================== TASKS ====================

class TaskCategorySerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskCategory
        fields = '__all__'
    
    def get_task_count(self, obj):
        return obj.projecttask_set.count()


class TaskDependencySerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='task.title', read_only=True)
    depends_on_title = serializers.CharField(source='depends_on.title', read_only=True)
    
    class Meta:
        model = TaskDependency
        fields = '__all__'


class ProjectTaskListSerializer(serializers.ModelSerializer):
    """Lightweight task serializer for lists"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.user.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    phase_name = serializers.CharField(source='phase.name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ProjectTask
        fields = [
            'id', 'task_code', 'title', 'project', 'project_name', 'project_code',
            'status', 'priority', 'progress_percentage',
            'assigned_to', 'assigned_to_name', 'category', 'category_name',
            'phase', 'phase_name', 'start_date', 'due_date',
            'estimated_hours', 'actual_hours', 'is_overdue', 'created_at'
        ]


class ProjectTaskSerializer(serializers.ModelSerializer):
    """Full task serializer"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    phase_name = serializers.CharField(source='phase.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    parent_task_title = serializers.CharField(source='parent_task.title', read_only=True)
    
    assigned_to_details = EmployeeProfileSerializer(source='assigned_to', read_only=True)
    created_by_name = serializers.CharField(source='created_by.user.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.user.get_full_name', read_only=True)
    
    documents = DocumentSerializer(many=True, read_only=True)
    
    subtasks = serializers.SerializerMethodField()
    dependencies = TaskDependencySerializer(many=True, read_only=True)
    dependent_tasks = TaskDependencySerializer(many=True, read_only=True)
    
    is_overdue = serializers.BooleanField(read_only=True)
    hours_variance = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectTask
        fields = '__all__'
    
    def get_subtasks(self, obj):
        subtasks = obj.subtasks.all()
        return ProjectTaskListSerializer(subtasks, many=True).data
    
    def get_hours_variance(self, obj):
        if obj.estimated_hours and obj.actual_hours:
            return float(obj.estimated_hours - obj.actual_hours)
        return None


# ==================== RESOURCES ====================

class ResourceCategorySerializer(serializers.ModelSerializer):
    resource_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ResourceCategory
        fields = '__all__'
    
    def get_resource_count(self, obj):
        return obj.projectresource_set.count()


class ProjectResourceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    total_allocated = serializers.SerializerMethodField()
    total_value = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectResource
        fields = '__all__'
    
    def get_total_allocated(self, obj):
        return obj.allocations.aggregate(
            total=Sum('quantity_allocated')
        )['total'] or 0
    
    def get_total_value(self, obj):
        return float(obj.quantity_available * obj.unit_cost)


class ProjectResourceAllocationSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    resource_name = serializers.CharField(source='resource.name', read_only=True)
    resource_code = serializers.CharField(source='resource.code', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    allocated_by_name = serializers.CharField(source='allocated_by.user.get_full_name', read_only=True)
    
    quantity_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectResourceAllocation
        fields = '__all__'
    
    def get_quantity_remaining(self, obj):
        return float(obj.quantity_allocated - obj.quantity_used)


# ==================== BUDGET & COSTS ====================

class BudgetCategorySerializer(serializers.ModelSerializer):
    total_budgeted = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    
    class Meta:
        model = BudgetCategory
        fields = '__all__'
    
    def get_total_budgeted(self, obj):
        return obj.projectbudgetline_set.aggregate(
            total=Sum('budgeted_amount')
        )['total'] or 0
    
    def get_total_spent(self, obj):
        return obj.projectbudgetline_set.aggregate(
            total=Sum('actual_amount')
        )['total'] or 0


class ProjectBudgetLineSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_code = serializers.CharField(source='category.code', read_only=True)
    phase_name = serializers.CharField(source='phase.name', read_only=True)
    
    variance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    available_budget = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    utilization_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectBudgetLine
        fields = '__all__'
    
    def get_utilization_percentage(self, obj):
        if obj.budgeted_amount > 0:
            return float((obj.actual_amount / obj.budgeted_amount) * 100)
        return 0


class ProjectExpenseSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    budget_line_description = serializers.CharField(source='budget_line.description', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.user.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.user.get_full_name', read_only=True)
    
    documents = DocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProjectExpense
        fields = '__all__'


# ==================== PERMITS & APPROVALS ====================

class PermitTypeSerializer(serializers.ModelSerializer):
    active_permits_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PermitType
        fields = '__all__'
    
    def get_active_permits_count(self, obj):
        return obj.projectpermit_set.exclude(
            status__in=['rejected', 'expired']
        ).count()


class ProjectPermitSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    permit_type_name = serializers.CharField(source='permit_type.name', read_only=True)
    responsible_person_name = serializers.CharField(
        source='responsible_person.user.get_full_name',
        read_only=True
    )
    
    documents = DocumentSerializer(many=True, read_only=True)
    
    days_to_expiry = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectPermit
        fields = '__all__'
    
    def get_days_to_expiry(self, obj):
        if obj.expiry_date and obj.status == 'approved':
            from django.utils import timezone
            delta = obj.expiry_date - timezone.now().date()
            return delta.days
        return None
    
    def get_is_expired(self, obj):
        if obj.expiry_date:
            from django.utils import timezone
            return timezone.now().date() > obj.expiry_date
        return False


# ==================== QUALITY & INSPECTIONS ====================

class InspectionTypeSerializer(serializers.ModelSerializer):
    inspection_count = serializers.SerializerMethodField()
    
    class Meta:
        model = InspectionType
        fields = '__all__'
    
    def get_inspection_count(self, obj):
        return obj.projectinspection_set.count()


class ProjectInspectionSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    inspection_type_name = serializers.CharField(source='inspection_type.name', read_only=True)
    phase_name = serializers.CharField(source='phase.name', read_only=True)
    conducted_by_name = serializers.CharField(source='conducted_by.user.get_full_name', read_only=True)
    
    documents = DocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProjectInspection
        fields = '__all__'


# ==================== RISKS & ISSUES ====================

class ProjectRiskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    identified_by_name = serializers.CharField(source='identified_by.user.get_full_name', read_only=True)
    owner_name = serializers.CharField(source='owner.user.get_full_name', read_only=True)
    
    risk_score = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectRisk
        fields = '__all__'
    
    def get_risk_score(self, obj):
        # Simple risk scoring: probability x impact
        prob_scores = {'very_low': 1, 'low': 2, 'medium': 3, 'high': 4, 'very_high': 5}
        impact_scores = {'negligible': 1, 'minor': 2, 'moderate': 3, 'major': 4, 'critical': 5}
        
        prob = prob_scores.get(obj.probability, 0)
        impact = impact_scores.get(obj.impact, 0)
        
        return prob * impact


class ProjectIssueSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    related_task_title = serializers.CharField(source='related_task.title', read_only=True)
    reported_by_name = serializers.CharField(source='reported_by.user.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.user.get_full_name', read_only=True)
    
    documents = DocumentSerializer(many=True, read_only=True)
    
    resolution_time = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectIssue
        fields = '__all__'
    
    def get_resolution_time(self, obj):
        if obj.resolved_date:
            delta = obj.resolved_date - obj.reported_date
            return delta.days
        return None


# ==================== CHANGE ORDERS ====================

class ChangeOrderSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.user.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.user.get_full_name', read_only=True)
    
    documents = DocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChangeOrder
        fields = '__all__'


# ==================== DAILY REPORTS ====================

class DailyProgressReportSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.user.get_full_name', read_only=True)
    
    documents = DocumentSerializer(many=True, read_only=True)
    
    total_workers = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyProgressReport
        fields = '__all__'
    
    def get_total_workers(self, obj):
        return obj.workers_onsite + obj.contractors_onsite


# ==================== MEETINGS ====================

class ProjectMeetingSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    organizer_name = serializers.CharField(source='organizer.user.get_full_name', read_only=True)
    
    attendee_details = EmployeeProfileSerializer(source='attendees', many=True, read_only=True)
    attendee_count = serializers.IntegerField(source='attendees.count', read_only=True)
    
    documents = DocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProjectMeeting
        fields = '__all__'


# ==================== SAFETY ====================

class SafetyIncidentSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    reported_by_name = serializers.CharField(source='reported_by.user.get_full_name', read_only=True)
    investigated_by_name = serializers.CharField(source='investigated_by.user.get_full_name', read_only=True)
    
    documents = DocumentSerializer(many=True, read_only=True)
    
    days_since_incident = serializers.SerializerMethodField()
    
    class Meta:
        model = SafetyIncident
        fields = '__all__'
    
    def get_days_since_incident(self, obj):
        from django.utils import timezone
        delta = timezone.now() - obj.incident_date
        return delta.days


# ==================== DASHBOARD & ANALYTICS ====================

class ProjectDashboardSerializer(serializers.Serializer):
    """Serializer for project dashboard statistics"""
    total_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    completed_projects = serializers.IntegerField()
    delayed_projects = serializers.IntegerField()
    
    total_budget = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_spent = serializers.DecimalField(max_digits=15, decimal_places=2)
    budget_variance = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    
    active_risks = serializers.IntegerField()
    open_issues = serializers.IntegerField()
    pending_change_orders = serializers.IntegerField()
    
    projects_by_status = serializers.DictField()
    projects_by_priority = serializers.DictField()