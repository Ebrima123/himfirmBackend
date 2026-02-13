# projects/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # Land & Property
    LandParcelViewSet,
    
    # Project Core
    ProjectTypeViewSet,
    ProjectViewSet,
    ProjectTeamMemberViewSet,
    
    # Phases & Milestones
    ProjectPhaseViewSet,
    ProjectMilestoneViewSet,
    
    # Tasks
    TaskCategoryViewSet,
    ProjectTaskViewSet,
    TaskDependencyViewSet,
    
    # Resources
    ResourceCategoryViewSet,
    ProjectResourceViewSet,
    ProjectResourceAllocationViewSet,
    
    # Budget & Costs
    BudgetCategoryViewSet,
    ProjectBudgetLineViewSet,
    ProjectExpenseViewSet,
    
    # Permits & Approvals
    PermitTypeViewSet,
    ProjectPermitViewSet,
    
    # Quality & Inspections
    InspectionTypeViewSet,
    ProjectInspectionViewSet,
    
    # Risks & Issues
    ProjectRiskViewSet,
    ProjectIssueViewSet,
    
    # Change Orders
    ChangeOrderViewSet,
    
    # Daily Reports
    DailyProgressReportViewSet,
    
    # Meetings
    ProjectMeetingViewSet,
    
    # Safety
    SafetyIncidentViewSet,
)

# Initialize router
router = DefaultRouter()

# ==================== LAND & PROPERTY ====================
router.register(r'land-parcels', LandParcelViewSet, basename='landparcel')

# ==================== PROJECT CORE ====================
router.register(r'project-types', ProjectTypeViewSet, basename='projecttype')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'team-members', ProjectTeamMemberViewSet, basename='teammember')

# ==================== PHASES & MILESTONES ====================
router.register(r'phases', ProjectPhaseViewSet, basename='phase')
router.register(r'milestones', ProjectMilestoneViewSet, basename='milestone')

# ==================== TASKS ====================
router.register(r'task-categories', TaskCategoryViewSet, basename='taskcategory')
router.register(r'tasks', ProjectTaskViewSet, basename='task')
router.register(r'task-dependencies', TaskDependencyViewSet, basename='taskdependency')

# ==================== RESOURCES ====================
router.register(r'resource-categories', ResourceCategoryViewSet, basename='resourcecategory')
router.register(r'resources', ProjectResourceViewSet, basename='resource')
router.register(r'resource-allocations', ProjectResourceAllocationViewSet, basename='resourceallocation')

# ==================== BUDGET & COSTS ====================
router.register(r'budget-categories', BudgetCategoryViewSet, basename='budgetcategory')
router.register(r'budget-lines', ProjectBudgetLineViewSet, basename='budgetline')
router.register(r'expenses', ProjectExpenseViewSet, basename='expense')

# ==================== PERMITS & APPROVALS ====================
router.register(r'permit-types', PermitTypeViewSet, basename='permittype')
router.register(r'permits', ProjectPermitViewSet, basename='permit')

# ==================== QUALITY & INSPECTIONS ====================
router.register(r'inspection-types', InspectionTypeViewSet, basename='inspectiontype')
router.register(r'inspections', ProjectInspectionViewSet, basename='inspection')

# ==================== RISKS & ISSUES ====================
router.register(r'risks', ProjectRiskViewSet, basename='risk')
router.register(r'issues', ProjectIssueViewSet, basename='issue')

# ==================== CHANGE ORDERS ====================
router.register(r'change-orders', ChangeOrderViewSet, basename='changeorder')

# ==================== DAILY REPORTS ====================
router.register(r'daily-reports', DailyProgressReportViewSet, basename='dailyreport')

# ==================== MEETINGS ====================
router.register(r'meetings', ProjectMeetingViewSet, basename='meeting')

# ==================== SAFETY ====================
router.register(r'safety-incidents', SafetyIncidentViewSet, basename='safetyincident')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]

# ==================== API ENDPOINT DOCUMENTATION ====================
"""
Complete API Endpoints for Project Management Module:

LAND & PROPERTY:
- GET    /api/projects/land-parcels/                          - List all land parcels
- POST   /api/projects/land-parcels/                          - Create land parcel
- GET    /api/projects/land-parcels/{id}/                     - Retrieve land parcel
- PUT    /api/projects/land-parcels/{id}/                     - Update land parcel
- PATCH  /api/projects/land-parcels/{id}/                     - Partial update
- DELETE /api/projects/land-parcels/{id}/                     - Delete land parcel
- GET    /api/projects/land-parcels/statistics/               - Get statistics
- GET    /api/projects/land-parcels/{id}/projects/            - Get projects on parcel

PROJECT CORE:
- GET    /api/projects/project-types/                         - List project types
- POST   /api/projects/project-types/                         - Create project type
- GET    /api/projects/project-types/{id}/                    - Retrieve project type
- PUT    /api/projects/project-types/{id}/                    - Update project type
- DELETE /api/projects/project-types/{id}/                    - Delete project type

- GET    /api/projects/projects/                              - List all projects
- POST   /api/projects/projects/                              - Create project
- GET    /api/projects/projects/{id}/                         - Retrieve project
- PUT    /api/projects/projects/{id}/                         - Update project
- PATCH  /api/projects/projects/{id}/                         - Partial update
- DELETE /api/projects/projects/{id}/                         - Delete project
- GET    /api/projects/projects/dashboard/                    - Project dashboard stats
- GET    /api/projects/projects/{id}/timeline/                - Get project timeline
- GET    /api/projects/projects/{id}/financial_summary/       - Get financial summary
- POST   /api/projects/projects/{id}/update_progress/         - Update progress %

- GET    /api/projects/team-members/                          - List team members
- POST   /api/projects/team-members/                          - Add team member
- GET    /api/projects/team-members/{id}/                     - Retrieve team member
- PUT    /api/projects/team-members/{id}/                     - Update team member
- DELETE /api/projects/team-members/{id}/                     - Remove team member

PHASES & MILESTONES:
- GET    /api/projects/phases/                                - List all phases
- POST   /api/projects/phases/                                - Create phase
- GET    /api/projects/phases/{id}/                           - Retrieve phase
- PUT    /api/projects/phases/{id}/                           - Update phase
- DELETE /api/projects/phases/{id}/                           - Delete phase
- POST   /api/projects/phases/{id}/update_progress/           - Update phase progress

- GET    /api/projects/milestones/                            - List all milestones
- POST   /api/projects/milestones/                            - Create milestone
- GET    /api/projects/milestones/{id}/                       - Retrieve milestone
- PUT    /api/projects/milestones/{id}/                       - Update milestone
- DELETE /api/projects/milestones/{id}/                       - Delete milestone
- GET    /api/projects/milestones/upcoming/                   - Get upcoming milestones

TASKS:
- GET    /api/projects/task-categories/                       - List task categories
- POST   /api/projects/task-categories/                       - Create category
- GET    /api/projects/task-categories/{id}/                  - Retrieve category
- PUT    /api/projects/task-categories/{id}/                  - Update category
- DELETE /api/projects/task-categories/{id}/                  - Delete category

- GET    /api/projects/tasks/                                 - List all tasks
- POST   /api/projects/tasks/                                 - Create task
- GET    /api/projects/tasks/{id}/                            - Retrieve task
- PUT    /api/projects/tasks/{id}/                            - Update task
- PATCH  /api/projects/tasks/{id}/                            - Partial update
- DELETE /api/projects/tasks/{id}/                            - Delete task
- POST   /api/projects/tasks/{id}/complete/                   - Mark task complete
- POST   /api/projects/tasks/{id}/approve/                    - Approve task

- GET    /api/projects/task-dependencies/                     - List dependencies
- POST   /api/projects/task-dependencies/                     - Create dependency
- GET    /api/projects/task-dependencies/{id}/                - Retrieve dependency
- DELETE /api/projects/task-dependencies/{id}/                - Delete dependency

RESOURCES:
- GET    /api/projects/resource-categories/                   - List resource categories
- POST   /api/projects/resource-categories/                   - Create category
- GET    /api/projects/resource-categories/{id}/              - Retrieve category
- PUT    /api/projects/resource-categories/{id}/              - Update category
- DELETE /api/projects/resource-categories/{id}/              - Delete category

- GET    /api/projects/resources/                             - List all resources
- POST   /api/projects/resources/                             - Create resource
- GET    /api/projects/resources/{id}/                        - Retrieve resource
- PUT    /api/projects/resources/{id}/                        - Update resource
- DELETE /api/projects/resources/{id}/                        - Delete resource
- GET    /api/projects/resources/low_stock/                   - Get low stock resources

- GET    /api/projects/resource-allocations/                  - List allocations
- POST   /api/projects/resource-allocations/                  - Create allocation
- GET    /api/projects/resource-allocations/{id}/             - Retrieve allocation
- PUT    /api/projects/resource-allocations/{id}/             - Update allocation
- DELETE /api/projects/resource-allocations/{id}/             - Delete allocation

BUDGET & COSTS:
- GET    /api/projects/budget-categories/                     - List budget categories
- POST   /api/projects/budget-categories/                     - Create category
- GET    /api/projects/budget-categories/{id}/                - Retrieve category
- PUT    /api/projects/budget-categories/{id}/                - Update category
- DELETE /api/projects/budget-categories/{id}/                - Delete category

- GET    /api/projects/budget-lines/                          - List budget lines
- POST   /api/projects/budget-lines/                          - Create budget line
- GET    /api/projects/budget-lines/{id}/                     - Retrieve budget line
- PUT    /api/projects/budget-lines/{id}/                     - Update budget line
- DELETE /api/projects/budget-lines/{id}/                     - Delete budget line

- GET    /api/projects/expenses/                              - List all expenses
- POST   /api/projects/expenses/                              - Create expense
- GET    /api/projects/expenses/{id}/                         - Retrieve expense
- PUT    /api/projects/expenses/{id}/                         - Update expense
- DELETE /api/projects/expenses/{id}/                         - Delete expense
- POST   /api/projects/expenses/{id}/approve/                 - Approve expense
- POST   /api/projects/expenses/{id}/mark_paid/               - Mark expense as paid

PERMITS & APPROVALS:
- GET    /api/projects/permit-types/                          - List permit types
- POST   /api/projects/permit-types/                          - Create permit type
- GET    /api/projects/permit-types/{id}/                     - Retrieve permit type
- PUT    /api/projects/permit-types/{id}/                     - Update permit type
- DELETE /api/projects/permit-types/{id}/                     - Delete permit type

- GET    /api/projects/permits/                               - List all permits
- POST   /api/projects/permits/                               - Create permit
- GET    /api/projects/permits/{id}/                          - Retrieve permit
- PUT    /api/projects/permits/{id}/                          - Update permit
- DELETE /api/projects/permits/{id}/                          - Delete permit
- GET    /api/projects/permits/expiring_soon/                 - Get expiring permits

QUALITY & INSPECTIONS:
- GET    /api/projects/inspection-types/                      - List inspection types
- POST   /api/projects/inspection-types/                      - Create type
- GET    /api/projects/inspection-types/{id}/                 - Retrieve type
- PUT    /api/projects/inspection-types/{id}/                 - Update type
- DELETE /api/projects/inspection-types/{id}/                 - Delete type

- GET    /api/projects/inspections/                           - List all inspections
- POST   /api/projects/inspections/                           - Create inspection
- GET    /api/projects/inspections/{id}/                      - Retrieve inspection
- PUT    /api/projects/inspections/{id}/                      - Update inspection
- DELETE /api/projects/inspections/{id}/                      - Delete inspection
- GET    /api/projects/inspections/upcoming/                  - Get upcoming inspections

RISKS & ISSUES:
- GET    /api/projects/risks/                                 - List all risks
- POST   /api/projects/risks/                                 - Create risk
- GET    /api/projects/risks/{id}/                            - Retrieve risk
- PUT    /api/projects/risks/{id}/                            - Update risk
- DELETE /api/projects/risks/{id}/                            - Delete risk
- GET    /api/projects/risks/high_priority/                   - Get high priority risks

- GET    /api/projects/issues/                                - List all issues
- POST   /api/projects/issues/                                - Create issue
- GET    /api/projects/issues/{id}/                           - Retrieve issue
- PUT    /api/projects/issues/{id}/                           - Update issue
- DELETE /api/projects/issues/{id}/                           - Delete issue
- POST   /api/projects/issues/{id}/resolve/                   - Mark issue resolved

CHANGE ORDERS:
- GET    /api/projects/change-orders/                         - List change orders
- POST   /api/projects/change-orders/                         - Create change order
- GET    /api/projects/change-orders/{id}/                    - Retrieve change order
- PUT    /api/projects/change-orders/{id}/                    - Update change order
- DELETE /api/projects/change-orders/{id}/                    - Delete change order
- POST   /api/projects/change-orders/{id}/submit/             - Submit for review
- POST   /api/projects/change-orders/{id}/approve/            - Approve change order

DAILY REPORTS:
- GET    /api/projects/daily-reports/                         - List daily reports
- POST   /api/projects/daily-reports/                         - Create daily report
- GET    /api/projects/daily-reports/{id}/                    - Retrieve report
- PUT    /api/projects/daily-reports/{id}/                    - Update report
- DELETE /api/projects/daily-reports/{id}/                    - Delete report

MEETINGS:
- GET    /api/projects/meetings/                              - List all meetings
- POST   /api/projects/meetings/                              - Create meeting
- GET    /api/projects/meetings/{id}/                         - Retrieve meeting
- PUT    /api/projects/meetings/{id}/                         - Update meeting
- DELETE /api/projects/meetings/{id}/                         - Delete meeting
- GET    /api/projects/meetings/upcoming/                     - Get upcoming meetings

SAFETY:
- GET    /api/projects/safety-incidents/                      - List incidents
- POST   /api/projects/safety-incidents/                      - Create incident
- GET    /api/projects/safety-incidents/{id}/                 - Retrieve incident
- PUT    /api/projects/safety-incidents/{id}/                 - Update incident
- DELETE /api/projects/safety-incidents/{id}/                 - Delete incident
- GET    /api/projects/safety-incidents/statistics/           - Get safety statistics

QUERY PARAMETERS (where applicable):
- ?status=value                   - Filter by status
- ?priority=value                 - Filter by priority
- ?project={id}                   - Filter by project
- ?search=term                    - Search across fields
- ?ordering=field                 - Order results
- ?page={n}                       - Pagination
- ?page_size={n}                  - Items per page
- ?quick_filter=value             - Quick filter presets
  - available                     - Available land parcels
  - in_development                - Land in development
  - active                        - Active projects
  - delayed                       - Delayed projects
  - my_projects                   - User's projects
  - my_tasks                      - User's tasks
  - overdue                       - Overdue tasks
  - due_soon                      - Tasks due within 7 days

EXAMPLES:
# Get all active projects
GET /api/projects/projects/?quick_filter=active

# Get my overdue tasks
GET /api/projects/tasks/?quick_filter=overdue&view=my_tasks

# Search projects by name
GET /api/projects/projects/?search=residential

# Get project financial summary
GET /api/projects/projects/123/financial_summary/

# Get upcoming milestones in next 30 days
GET /api/projects/milestones/upcoming/?days=30

# Get permits expiring soon
GET /api/projects/permits/expiring_soon/?days=60

# Filter expenses by project and status
GET /api/projects/expenses/?project=123&payment_status=pending

# Get project dashboard
GET /api/projects/projects/dashboard/

# Complete a task
POST /api/projects/tasks/456/complete/

# Approve an expense
POST /api/projects/expenses/789/approve/

# Get low stock resources
GET /api/projects/resources/low_stock/

# Get high priority risks
GET /api/projects/risks/high_priority/

# Get safety statistics
GET /api/projects/safety-incidents/statistics/
"""