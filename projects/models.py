# projects/models.py
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from core.models import EmployeeProfile
from documents.models import Document


# ==================== LAND & PROPERTY ====================

class LandParcel(models.Model):
    """Land parcels available for development"""
    ZONING_CHOICES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('mixed_use', 'Mixed Use'),
        ('agricultural', 'Agricultural'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('under_review', 'Under Review'),
        ('in_development', 'In Development'),
        ('allocated', 'Allocated'),
        ('sold', 'Sold'),
        ('on_hold', 'On Hold'),
    ]
    
    # Basic Information
    title_number = models.CharField(max_length=100, unique=True)
    plot_number = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='')
    
    # Size & Measurements
    size_sq_meters = models.DecimalField(max_digits=10, decimal_places=2)
    size_acres = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    frontage_meters = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    depth_meters = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    
    # Legal & Zoning
    zoning = models.CharField(max_length=50, choices=ZONING_CHOICES)
    zoning_details = models.TextField(blank=True)
    legal_description = models.TextField(blank=True)
    
    # Acquisition
    acquisition_date = models.DateField()
    acquisition_cost = models.DecimalField(max_digits=15, decimal_places=2)
    seller_name = models.CharField(max_length=200, blank=True)
    
    # Valuation
    current_market_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    last_valuation_date = models.DateField(blank=True, null=True)
    
    # Development Potential
    max_building_height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="In meters")
    max_floor_area_ratio = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    max_units_allowed = models.IntegerField(blank=True, null=True)
    
    # Utilities & Infrastructure
    has_water = models.BooleanField(default=False)
    has_electricity = models.BooleanField(default=False)
    has_sewage = models.BooleanField(default=False)
    has_gas = models.BooleanField(default=False)
    road_access = models.BooleanField(default=False)
    
    # Status & Notes
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='available')
    notes = models.TextField(blank=True)
    
    # Coordinates (for mapping)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Documents & Media
    documents = GenericRelation(Document)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Land Parcel'
        verbose_name_plural = 'Land Parcels'
    
    def __str__(self):
        return f"{self.title_number} - {self.location}"


# ==================== PROJECT CORE ====================

class ProjectType(models.Model):
    """Types of construction projects"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class Project(models.Model):
    """Main project entity"""
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('design', 'Design'),
        ('pre_construction', 'Pre-Construction'),
        ('permits', 'Permits & Approvals'),
        ('construction', 'Construction'),
        ('finishing', 'Finishing'),
        ('inspection', 'Inspection'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    project_type = models.ForeignKey(ProjectType, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    
    # Land & Location
    land_parcel = models.ForeignKey(LandParcel, on_delete=models.SET_NULL, null=True, blank=True)
    additional_location_info = models.TextField(blank=True)
    
    # Team
    manager = models.ForeignKey(
        EmployeeProfile, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='managed_projects'
    )
    architect = models.ForeignKey(
        EmployeeProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='architect_projects'
    )
    engineer = models.ForeignKey(
        EmployeeProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='engineer_projects'
    )
    site_supervisor = models.ForeignKey(
        EmployeeProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='supervised_projects'
    )
    team_members = models.ManyToManyField(
        EmployeeProfile,
        through='ProjectTeamMember',
        related_name='team_projects'
    )
    
    # Timeline
    start_date = models.DateField()
    expected_completion = models.DateField(null=True, blank=True)
    actual_completion = models.DateField(null=True, blank=True)
    
    # Budget & Financial
    budget = models.DecimalField(max_digits=15, decimal_places=2)
    contingency_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Status & Progress
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='planning')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    progress_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Project Details
    total_units = models.IntegerField(blank=True, null=True, help_text="Number of units (apartments, houses, etc.)")
    total_floors = models.IntegerField(blank=True, null=True)
    total_area_sq_meters = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Client/Owner Information
    client_name = models.CharField(max_length=200, blank=True)
    client_contact = models.CharField(max_length=200, blank=True)
    
    # Notes & Documents
    notes = models.TextField(blank=True)
    documents = GenericRelation(Document)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('can_approve_project', 'Can approve project'),
            ('can_close_project', 'Can close project'),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_delayed(self):
        if self.expected_completion and self.status not in ['completed', 'cancelled']:
            return timezone.now().date() > self.expected_completion
        return False
    
    @property
    def budget_variance(self):
        return self.budget - self.actual_cost


class ProjectTeamMember(models.Model):
    """Team members assigned to projects with roles"""
    ROLE_CHOICES = [
        ('project_manager', 'Project Manager'),
        ('architect', 'Architect'),
        ('engineer', 'Engineer'),
        ('site_supervisor', 'Site Supervisor'),
        ('foreman', 'Foreman'),
        ('safety_officer', 'Safety Officer'),
        ('quality_inspector', 'Quality Inspector'),
        ('surveyor', 'Surveyor'),
        ('estimator', 'Estimator'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    assigned_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['project', 'employee', 'role']
    
    def __str__(self):
        return f"{self.employee} - {self.role} on {self.project}"


# ==================== PROJECT PHASES & MILESTONES ====================

class ProjectPhase(models.Model):
    """Major phases in a project"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='phases')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sequence = models.IntegerField(default=1)
    
    start_date = models.DateField()
    end_date = models.DateField()
    actual_start_date = models.DateField(blank=True, null=True)
    actual_end_date = models.DateField(blank=True, null=True)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='not_started')
    progress_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['project', 'sequence']
        unique_together = ['project', 'sequence']
    
    def __str__(self):
        return f"{self.project.code} - Phase {self.sequence}: {self.name}"


class ProjectMilestone(models.Model):
    """Key milestones in projects"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('achieved', 'Achieved'),
        ('missed', 'Missed'),
        ('cancelled', 'Cancelled'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    phase = models.ForeignKey(ProjectPhase, on_delete=models.CASCADE, related_name='milestones', blank=True, null=True)
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_date = models.DateField()
    actual_date = models.DateField(blank=True, null=True)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    is_critical = models.BooleanField(default=False)
    
    responsible_person = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    notes = models.TextField(blank=True)
    documents = GenericRelation(Document)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['project', 'target_date']
    
    def __str__(self):
        return f"{self.project.code} - {self.name}"


# ==================== TASKS & ACTIVITIES ====================

class TaskCategory(models.Model):
    """Categories for organizing tasks"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color_code = models.CharField(max_length=7, blank=True, help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Task Categories'
    
    def __str__(self):
        return self.name


class ProjectTask(models.Model):
    """Individual tasks within projects"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Relationships
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    phase = models.ForeignKey(ProjectPhase, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, null=True, blank=True)
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtasks')
    
    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    task_code = models.CharField(max_length=50, blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(
        EmployeeProfile, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks'
    )
    
    # Timeline
    start_date = models.DateField(blank=True, null=True)
    due_date = models.DateField()
    completed_date = models.DateField(blank=True, null=True)
    
    # Estimated vs Actual
    estimated_hours = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    actual_hours = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    
    # Status & Progress
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    progress_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Additional Fields
    is_billable = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_tasks'
    )
    approval_date = models.DateTimeField(blank=True, null=True)
    
    notes = models.TextField(blank=True)
    documents = GenericRelation(Document)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['project', '-priority', 'due_date']
    
    def __str__(self):
        return f"{self.project.code} - {self.title}"
    
    @property
    def is_overdue(self):
        if self.status not in ['completed', 'cancelled']:
            return timezone.now().date() > self.due_date
        return False


class TaskDependency(models.Model):
    """Dependencies between tasks"""
    DEPENDENCY_TYPES = [
        ('finish_to_start', 'Finish to Start'),
        ('start_to_start', 'Start to Start'),
        ('finish_to_finish', 'Finish to Finish'),
        ('start_to_finish', 'Start to Finish'),
    ]
    
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE, related_name='dependencies')
    depends_on = models.ForeignKey(ProjectTask, on_delete=models.CASCADE, related_name='dependent_tasks')
    dependency_type = models.CharField(max_length=50, choices=DEPENDENCY_TYPES, default='finish_to_start')
    lag_days = models.IntegerField(default=0, help_text="Number of days delay after dependency")
    
    class Meta:
        unique_together = ['task', 'depends_on']
        verbose_name_plural = 'Task Dependencies'
    
    def __str__(self):
        return f"{self.task} depends on {self.depends_on}"


# ==================== RESOURCES & EQUIPMENT ====================

class ResourceCategory(models.Model):
    """Categories for resources"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Resource Categories'
    
    def __str__(self):
        return self.name


class ProjectResource(models.Model):
    """Resources (equipment, materials, etc.) used in projects"""
    RESOURCE_TYPES = [
        ('equipment', 'Equipment'),
        ('material', 'Material'),
        ('labor', 'Labor'),
        ('vehicle', 'Vehicle'),
        ('tool', 'Tool'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPES)
    category = models.ForeignKey(ResourceCategory, on_delete=models.SET_NULL, null=True, blank=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    unit_of_measure = models.CharField(max_length=50)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2)
    
    quantity_available = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class ProjectResourceAllocation(models.Model):
    """Allocation of resources to projects"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='resource_allocations')
    resource = models.ForeignKey(ProjectResource, on_delete=models.CASCADE, related_name='allocations')
    task = models.ForeignKey(ProjectTask, on_delete=models.SET_NULL, null=True, blank=True, related_name='resource_allocations')
    
    quantity_allocated = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    allocation_date = models.DateField()
    expected_return_date = models.DateField(blank=True, null=True)
    actual_return_date = models.DateField(blank=True, null=True)
    
    cost_per_unit = models.DecimalField(max_digits=15, decimal_places=2)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2)
    
    allocated_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-allocation_date']
    
    def __str__(self):
        return f"{self.resource.name} allocated to {self.project.code}"
    
    def save(self, *args, **kwargs):
        self.total_cost = self.quantity_allocated * self.cost_per_unit
        super().save(*args, **kwargs)


# ==================== BUDGET & COSTS ====================

class BudgetCategory(models.Model):
    """Categories for budget items"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Budget Categories'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class ProjectBudgetLine(models.Model):
    """Detailed budget line items for projects"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='budget_lines')
    category = models.ForeignKey(BudgetCategory, on_delete=models.SET_NULL, null=True)
    phase = models.ForeignKey(ProjectPhase, on_delete=models.SET_NULL, null=True, blank=True)
    
    description = models.CharField(max_length=200)
    budgeted_amount = models.DecimalField(max_digits=15, decimal_places=2)
    actual_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    committed_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['project', 'category']
    
    def __str__(self):
        return f"{self.project.code} - {self.description}"
    
    @property
    def variance(self):
        return self.budgeted_amount - self.actual_amount
    
    @property
    def available_budget(self):
        return self.budgeted_amount - self.committed_amount - self.actual_amount


class ProjectExpense(models.Model):
    """Actual expenses incurred on projects"""
    EXPENSE_TYPES = [
        ('material', 'Material'),
        ('labor', 'Labor'),
        ('equipment', 'Equipment'),
        ('subcontractor', 'Subcontractor'),
        ('permit', 'Permit/License'),
        ('professional_fee', 'Professional Fee'),
        ('utility', 'Utility'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='expenses')
    budget_line = models.ForeignKey(ProjectBudgetLine, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(BudgetCategory, on_delete=models.SET_NULL, null=True)
    
    expense_type = models.CharField(max_length=50, choices=EXPENSE_TYPES)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    expense_date = models.DateField()
    invoice_number = models.CharField(max_length=100, blank=True)
    vendor_name = models.CharField(max_length=200, blank=True)
    
    payment_status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ], default='pending')
    
    approved_by = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_expenses'
    )
    approval_date = models.DateTimeField(blank=True, null=True)
    
    submitted_by = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='submitted_expenses'
    )
    
    notes = models.TextField(blank=True)
    documents = GenericRelation(Document)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-expense_date']
    
    def __str__(self):
        return f"{self.project.code} - {self.description} - ${self.amount}"


# ==================== PERMITS & APPROVALS ====================

class PermitType(models.Model):
    """Types of permits required"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    issuing_authority = models.CharField(max_length=200, blank=True)
    typical_processing_days = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class ProjectPermit(models.Model):
    """Permits and approvals for projects"""
    STATUS_CHOICES = [
        ('not_applied', 'Not Applied'),
        ('applied', 'Applied'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='permits')
    permit_type = models.ForeignKey(PermitType, on_delete=models.SET_NULL, null=True)
    
    permit_number = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    
    issuing_authority = models.CharField(max_length=200)
    application_date = models.DateField(blank=True, null=True)
    approval_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='not_applied')
    
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fee_paid = models.BooleanField(default=False)
    
    responsible_person = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    notes = models.TextField(blank=True)
    documents = GenericRelation(Document)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['project', '-application_date']
    
    def __str__(self):
        return f"{self.project.code} - {self.permit_type}"


# ==================== QUALITY & INSPECTIONS ====================

class InspectionType(models.Model):
    """Types of inspections"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class ProjectInspection(models.Model):
    """Quality inspections on projects"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('conditional', 'Conditional Pass'),
        ('cancelled', 'Cancelled'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='inspections')
    inspection_type = models.ForeignKey(InspectionType, on_delete=models.SET_NULL, null=True)
    phase = models.ForeignKey(ProjectPhase, on_delete=models.SET_NULL, null=True, blank=True)
    
    inspection_date = models.DateField()
    inspector_name = models.CharField(max_length=200)
    inspector_organization = models.CharField(max_length=200, blank=True)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='scheduled')
    
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    defects_found = models.TextField(blank=True)
    
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(blank=True, null=True)
    
    conducted_by = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_inspections'
    )
    
    documents = GenericRelation(Document)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-inspection_date']
    
    def __str__(self):
        return f"{self.project.code} - {self.inspection_type} - {self.inspection_date}"


# ==================== RISKS & ISSUES ====================

class ProjectRisk(models.Model):
    """Risk tracking for projects"""
    PROBABILITY_CHOICES = [
        ('very_low', 'Very Low'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High'),
    ]
    
    IMPACT_CHOICES = [
        ('negligible', 'Negligible'),
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('major', 'Major'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('identified', 'Identified'),
        ('analyzing', 'Analyzing'),
        ('mitigating', 'Mitigating'),
        ('monitoring', 'Monitoring'),
        ('occurred', 'Occurred'),
        ('closed', 'Closed'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='risks')
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    
    probability = models.CharField(max_length=20, choices=PROBABILITY_CHOICES)
    impact = models.CharField(max_length=20, choices=IMPACT_CHOICES)
    
    mitigation_strategy = models.TextField(blank=True)
    contingency_plan = models.TextField(blank=True)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='identified')
    
    identified_by = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='identified_risks'
    )
    owner = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_risks'
    )
    
    identified_date = models.DateField(auto_now_add=True)
    review_date = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-identified_date']
    
    def __str__(self):
        return f"{self.project.code} - {self.title}"


class ProjectIssue(models.Model):
    """Issues and problems encountered in projects"""
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('escalated', 'Escalated'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='issues')
    related_task = models.ForeignKey(ProjectTask, on_delete=models.SET_NULL, null=True, blank=True)
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='open')
    
    reported_by = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_issues'
    )
    assigned_to = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_issues'
    )
    
    reported_date = models.DateTimeField(auto_now_add=True)
    resolved_date = models.DateTimeField(blank=True, null=True)
    
    resolution = models.TextField(blank=True)
    
    documents = GenericRelation(Document)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-reported_date']
    
    def __str__(self):
        return f"{self.project.code} - {self.title}"


# ==================== CHANGE ORDERS ====================

class ChangeOrder(models.Model):
    """Change orders for project modifications"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='change_orders')
    
    change_order_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    reason = models.TextField()
    
    requested_by = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_change_orders'
    )
    
    cost_impact = models.DecimalField(max_digits=15, decimal_places=2)
    schedule_impact_days = models.IntegerField(default=0)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    
    submitted_date = models.DateField(blank=True, null=True)
    approved_date = models.DateField(blank=True, null=True)
    approved_by = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_change_orders'
    )
    
    implementation_date = models.DateField(blank=True, null=True)
    
    notes = models.TextField(blank=True)
    documents = GenericRelation(Document)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.change_order_number} - {self.title}"


# ==================== DAILY REPORTS & LOGS ====================

class DailyProgressReport(models.Model):
    """Daily progress reports from project sites"""
    WEATHER_CHOICES = [
        ('sunny', 'Sunny'),
        ('cloudy', 'Cloudy'),
        ('rainy', 'Rainy'),
        ('stormy', 'Stormy'),
        ('snowy', 'Snowy'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='daily_reports')
    
    report_date = models.DateField()
    submitted_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True)
    
    weather_condition = models.CharField(max_length=50, choices=WEATHER_CHOICES, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    
    work_performed = models.TextField()
    materials_used = models.TextField(blank=True)
    equipment_used = models.TextField(blank=True)
    
    workers_onsite = models.IntegerField(default=0)
    contractors_onsite = models.IntegerField(default=0)
    
    delays_encountered = models.TextField(blank=True)
    safety_incidents = models.TextField(blank=True)
    quality_issues = models.TextField(blank=True)
    
    visitors_onsite = models.TextField(blank=True)
    
    notes = models.TextField(blank=True)
    documents = GenericRelation(Document)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-report_date']
        unique_together = ['project', 'report_date']
    
    def __str__(self):
        return f"{self.project.code} - {self.report_date}"


# ==================== MEETINGS & COMMUNICATIONS ====================

class ProjectMeeting(models.Model):
    """Meetings related to projects"""
    MEETING_TYPES = [
        ('kickoff', 'Kickoff'),
        ('status', 'Status Update'),
        ('review', 'Review'),
        ('planning', 'Planning'),
        ('coordination', 'Coordination'),
        ('client', 'Client Meeting'),
        ('site_visit', 'Site Visit'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='meetings')
    
    title = models.CharField(max_length=200)
    meeting_type = models.CharField(max_length=50, choices=MEETING_TYPES)
    
    meeting_date = models.DateTimeField()
    duration_minutes = models.IntegerField()
    location = models.CharField(max_length=200, blank=True)
    
    organizer = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organized_meetings'
    )
    attendees = models.ManyToManyField(EmployeeProfile, related_name='attended_meetings', blank=True)
    
    agenda = models.TextField(blank=True)
    minutes = models.TextField(blank=True)
    action_items = models.TextField(blank=True)
    
    documents = GenericRelation(Document)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-meeting_date']
    
    def __str__(self):
        return f"{self.project.code} - {self.title} - {self.meeting_date.date()}"


# ==================== SAFETY ====================

class SafetyIncident(models.Model):
    """Safety incidents on project sites"""
    SEVERITY_CHOICES = [
        ('near_miss', 'Near Miss'),
        ('minor', 'Minor'),
        ('serious', 'Serious'),
        ('major', 'Major'),
        ('fatal', 'Fatal'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='safety_incidents')
    
    incident_date = models.DateTimeField()
    location = models.CharField(max_length=200)
    
    description = models.TextField()
    severity = models.CharField(max_length=50, choices=SEVERITY_CHOICES)
    
    persons_involved = models.TextField()
    injuries = models.TextField(blank=True)
    property_damage = models.TextField(blank=True)
    
    immediate_action_taken = models.TextField()
    root_cause = models.TextField(blank=True)
    corrective_actions = models.TextField(blank=True)
    
    reported_by = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_safety_incidents'
    )
    
    investigated_by = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='investigated_safety_incidents'
    )
    
    authorities_notified = models.BooleanField(default=False)
    
    documents = GenericRelation(Document)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-incident_date']
    
    def __str__(self):
        return f"{self.project.code} - {self.severity} - {self.incident_date.date()}"