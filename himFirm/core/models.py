# core/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    manager = models.ForeignKey('EmployeeProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)  # Make email unique and required for login
    phone = models.CharField(max_length=20, blank=True)
    is_mfa_enabled = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'          # <-- This tells Django to use email for login
    REQUIRED_FIELDS = ['username']    # Username still exists but not used for login

    def __str__(self):
        return self.email

class EmployeeProfile(models.Model):
    POSITION_CHOICES = [
        ('CEO', 'Chief Executive Officer'),
        ('EDBO', 'Executive Director of Business Operations'),
        ('Finance Manager', 'Finance & Accountant Manager'),
        ('Marketing Manager', 'Marketing & Sales Manager'),
        ('PR Manager', 'PR & CRM Manager'),
        ('Admin Manager', 'Admin & Records Manager'),
        ('Project Manager', 'PMDC Manager'),
        ('Production Manager', 'Production & Depot Manager'),
        ('Procurement Manager', 'Procurement & Purchasing Manager'),
        ('Audit Manager', 'Audit & Compliance Manager'),
        ('HR Manager', 'Human Resources / R&D Manager'),
        ('Accountant', 'Accountant'),
        ('Sales Officer', 'Sales / Marketing Officer'),
        ('Project Supervisor', 'Project Coordinator / Supervisor'),
        ('Receptionist', 'Receptionist'),
        ('Clerk', 'Clerk / Records Officer'),
        ('Driver', 'Driver'),
        ('Security', 'Security Guard'),
        ('Janitor', 'Janitor'),
        # Add others as needed
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.CharField(max_length=100, choices=POSITION_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='employees/', blank=True, null=True)
    reports_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    date_joined = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"