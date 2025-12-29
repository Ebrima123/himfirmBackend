# finance/models.py
from django.db import models
from crm.models import Allocation
from core.models import CustomUser, EmployeeProfile

class Invoice(models.Model):
    allocation = models.ForeignKey(Allocation, on_delete=models.PROTECT)
    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='unpaid', choices=[
        ('unpaid', 'Unpaid'), ('partial', 'Partially Paid'), ('paid', 'Paid')
    ])

    def __str__(self):
        return self.invoice_number

class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, null=True, blank=True)
    customer = models.ForeignKey('crm.Customer', on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50)
    received_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True)
    receipt_number = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"Payment {self.receipt_number} - {self.amount}"