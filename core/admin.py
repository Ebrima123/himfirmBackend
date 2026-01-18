# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import CustomUser, EmployeeProfile, Department

# Unregister the default Group admin if you don't need it customized
admin.site.unregister(Group)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager')
    search_fields = ('name',)
    list_filter = ('name',)
    ordering = ('name',)

class EmployeeProfileInline(admin.StackedInline):
    model = EmployeeProfile
    can_delete = False
    verbose_name_plural = 'Employee Profile'
    fk_name = 'user'
    fields = ('department', 'position', 'phone', 'photo', 'reports_to', 'is_active')
    readonly_fields = ('date_joined',)

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    inlines = (EmployeeProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_position', 'get_department', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__department', 'profile__position')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__phone')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    def get_position(self, obj):
        return obj.profile.position if hasattr(obj, 'profile') else '-'
    get_position.short_description = 'Position'

    def get_department(self, obj):
        return obj.profile.department.name if hasattr(obj, 'profile') and obj.profile.department else '-'
    get_department.short_description = 'Department'

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_full_name', 'position', 'department', 'reports_to', 'date_joined', 'is_active')
    list_filter = ('position', 'department', 'is_active', 'date_joined')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'phone')
    raw_id_fields = ('reports_to',)  # Useful for large number of employees
    readonly_fields = ('date_joined',)

    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Professional Info', {'fields': ('department', 'position', 'reports_to')}),
        ('Contact', {'fields': ('phone', 'photo')}),
        ('Status', {'fields': ('is_active', 'date_joined')}),
    )

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Full Name'