# finance/permissions.py
from rest_framework import permissions


class IsFinanceManager(permissions.BasePermission):
    """
    Permission check for finance manager role
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if user has finance manager role
        try:
            employee = request.user.employeeprofile
            return (
                employee.role in ['admin', 'finance_manager'] or
                request.user.is_superuser
            )
        except:
            return False


class IsAccountant(permissions.BasePermission):
    """
    Permission check for accountant role
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            employee = request.user.employeeprofile
            return (
                employee.role in ['admin', 'finance_manager', 'accountant'] or
                request.user.is_superuser
            )
        except:
            return False


class CanApproveExpenses(permissions.BasePermission):
    """
    Permission to approve expenses
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            employee = request.user.employeeprofile
            return (
                employee.role in ['admin', 'finance_manager', 'project_manager'] or
                request.user.is_superuser
            )
        except:
            return False


class CanManageVendors(permissions.BasePermission):
    """
    Permission to manage vendors
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        try:
            employee = request.user.employeeprofile
            return (
                employee.role in ['admin', 'finance_manager', 'procurement_manager'] or
                request.user.is_superuser
            )
        except:
            return False