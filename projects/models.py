# projects/models.py
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from core.models import EmployeeProfile
from documents.models import Document

class LandParcel(models.Model):
    title_number = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=200)
    size_sq_meters = models.DecimalField(max_digits=10, decimal_places=2)
    acquisition_date = models.DateField()
    acquisition_cost = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=50, choices=[
        ('available', 'Available'), ('in_development', 'In Development'), ('allocated', 'Allocated')
    ], default='available')
    documents = GenericRelation(Document)

    def __str__(self):
        return f"{self.title_number} - {self.location}"

class Project(models.Model):
    name = models.CharField(max_length=200)
    land_parcel = models.ForeignKey(LandParcel, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    start_date = models.DateField()
    expected_completion = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=15, decimal_places=2)
    manager = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=50, default='planning')
    documents = GenericRelation(Document)

    def __str__(self):
        return self.name

class ProjectTask(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True)
    due_date = models.DateField()
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed')
    ], default='pending')

    def __str__(self):
        return f"{self.project.name} - {self.title}"