# crm/models.py
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from core.models import CustomUser, EmployeeProfile
from projects.models import Project
from documents.models import Document

class Customer(models.Model):
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    national_id = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    date_registered = models.DateField(auto_now_add=True)
    documents = GenericRelation(Document)

    def __str__(self):
        return self.full_name

# crm/serializers.py
class LeadSerializer(serializers.ModelSerializer):
    # Use PrimaryKeyRelatedField correctly
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        write_only=True
    )
    
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=EmployeeProfile.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    
    customer_details = CustomerSerializer(source='customer', read_only=True)
    assigned_to_details = serializers.StringRelatedField(source='assigned_to', read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id',
            'customer',  # This is the ID when writing
            'customer_details',  # This is the full object when reading
            'source',
            'status',
            'notes',
            'assigned_to',  # This is the ID when writing
            'assigned_to_details',  # This is the string when reading
            'created_at',
        ]


class SiteVisit(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='visits')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    visit_date = models.DateTimeField()
    feedback = models.TextField(blank=True)
    attended_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Visit for {self.lead} on {self.visit_date.date()}"

class Allocation(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    plot_number = models.CharField(max_length=50)
    allocation_date = models.DateField(auto_now_add=True)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    documents = GenericRelation(Document)

    def __str__(self):
        return f"{self.customer} - Plot {self.plot_number}"