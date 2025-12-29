from django.db import models
class VisitorLog(models.Model):
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    purpose = models.TextField()
    time_in = models.DateTimeField(auto_now_add=True)
    time_out = models.DateTimeField(null=True, blank=True)

class Vehicle(models.Model):
    registration = models.CharField(max_length=50, unique=True)
    model = models.CharField(max_length=100)

class IncidentReport(models.Model):
    reported_by = models.ForeignKey('core.EmployeeProfile', on_delete=models.SET_NULL, null=True)
    incident_type = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=20, default='open')