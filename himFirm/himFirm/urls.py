# himfirm3/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication (Core)
    path('api/auth/', include('core.urls')),  # login, profile, refresh

    # Executive Level - Shared / Cross-Department
    path('api/documents/', include('documents.urls')),     # Used by everyone
    path('api/support/', include('support.urls')),         # Visitor logs, vehicles, incidents
    path('api/audit/', include('audit.urls')),             # Audit logs (CEO, EDBO, Audit Manager)

    # Senior Management Level
    path('api/hr/', include('employees.urls')),            # Human Resources / R&D
    path('api/pr-crm/', include('crm.urls')),              # PR & CRM Manager + POP Unit
    path('api/marketing-sales/', include('crm.urls')),     # Marketing & Sales (shared with PR-CRM for now)
    path('api/finance/', include('finance.urls')),         # Finance & Accountant Manager
    path('api/procurement/', include('procurement.urls')), # Procurement & Purchasing
    path('api/admin-records/', include('documents.urls')), # Admin & Records (re-use documents heavily)

    # Mid Management Level
    path('api/projects/', include('projects.urls')),       # PMDC Manager + PPD Unit
    path('api/production/', include('production.urls')),  # Production & Depot + BWU Unit

    # First Level / Entry
    # These can share the above endpoints based on permissions
    # e.g., Receptionist → /api/support/visitor-logs/
    # Drivers → /api/production/deliveries/ or /api/support/trips/
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)