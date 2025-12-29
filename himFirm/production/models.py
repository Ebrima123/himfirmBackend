# production/models.py
from django.db import models
from core.models import EmployeeProfile
from projects.models import Project

class RawMaterial(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name

class ProductionBatch(models.Model):
    batch_number = models.CharField(max_length=50, unique=True)
    production_date = models.DateField()
    bricks_produced = models.PositiveIntegerField()
    quality_status = models.CharField(max_length=30, choices=[
        ('good', 'Good'), ('defective', 'Defective'), ('pending', 'Pending')
    ], default='pending')
    inspected_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.batch_number

class BrickStock(models.Model):
    batch = models.ForeignKey(ProductionBatch, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    location = models.CharField(max_length=100)

class Delivery(models.Model):
    batch = models.ForeignKey(ProductionBatch, on_delete=models.PROTECT)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    delivery_date = models.DateField()
    driver = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True)
    received_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='received_deliveries')