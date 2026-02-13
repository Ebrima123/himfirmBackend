# finance/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from crm.models import Allocation, Customer
from core.models import CustomUser, EmployeeProfile
from django.conf import settings

# ==================== INVOICING & BILLING ====================

# finance/models.py (just the Invoice model part - replace your existing Invoice model)

class Invoice(models.Model):
    INVOICE_TYPE_CHOICES = [
        ('sale', 'Sales Invoice'),
        ('advance', 'Advance Invoice'),
        ('progress', 'Progress Billing'),
        ('final', 'Final Invoice'),
        ('retention', 'Retention Invoice'),
        ('credit_note', 'Credit Note'),
        ('debit_note', 'Debit Note'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('sent', 'Sent'),
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
        ('void', 'Void'),
    ]

    allocation = models.ForeignKey(Allocation, on_delete=models.PROTECT, null=True, blank=True, related_name='invoices')
    project = models.ForeignKey('projects.Project', on_delete=models.PROTECT, null=True, blank=True, related_name='finance_invoices')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True, related_name='invoices')  # Made nullable
    
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPE_CHOICES, default='sale')
    
    issue_date = models.DateField()
    due_date = models.DateField()
    
    # Financial fields
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Retention (common in construction)
    retention_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    retention_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Additional fields
    notes = models.TextField(blank=True, null=True)
    terms_and_conditions = models.TextField(blank=True, null=True)
    
    # Tracking
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices_created')
    approved_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices_approved')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        customer_name = self.customer.name if self.customer else "No Customer"
        return f"{self.invoice_number} - {customer_name}"

    @property
    def balance_due(self):
        return self.amount - self.paid_amount


class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit = models.CharField(max_length=50, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description}"


# ==================== PAYMENTS & RECEIPTS ====================

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('online', 'Online Payment'),
        ('pdc', 'Post Dated Cheque'),
        ('dd', 'Demand Draft'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('cleared', 'Cleared'),
        ('bounced', 'Bounced'),
        ('cancelled', 'Cancelled'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, null=True, blank=True, related_name='payments')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='payments')
    
    receipt_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    
    # Payment instrument details
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    cheque_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='cleared')
    
    received_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_received')
    deposited_to_account = models.ForeignKey('BankAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_deposited')
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)  # Changed from auto_now_add
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment {self.receipt_number} - {self.amount}"


# ==================== EXPENSES & VENDOR MANAGEMENT ====================

class Vendor(models.Model):
    VENDOR_TYPE_CHOICES = [
        ('contractor', 'Contractor'),
        ('supplier', 'Supplier'),
        ('subcontractor', 'Subcontractor'),
        ('consultant', 'Consultant'),
        ('service_provider', 'Service Provider'),
    ]

    name = models.CharField(max_length=200)
    vendor_code = models.CharField(max_length=50, unique=True)
    vendor_type = models.CharField(max_length=50, choices=VENDOR_TYPE_CHOICES)
    
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Tax details
    pan_number = models.CharField(max_length=20, blank=True, null=True)
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Banking
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Credit terms
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    payment_terms_days = models.IntegerField(default=30)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vendor_code} - {self.name}"


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('sent', 'Sent to Vendor'),
        ('partial', 'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled', 'Cancelled'),
    ]

    po_number = models.CharField(max_length=50, unique=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='purchase_orders')
    project = models.ForeignKey('projects.Project', on_delete=models.PROTECT, null=True, blank=True, related_name='purchase_orders')
    
    po_date = models.DateField()
    delivery_date = models.DateField()
    
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    delivery_address = models.TextField(blank=True, null=True)
    terms_and_conditions = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_created')
    approved_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_approved')
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.po_number} - {self.vendor}"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    received_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.description}"


class Expense(models.Model):
    EXPENSE_CATEGORY_CHOICES = [
        ('material', 'Material'),
        ('labor', 'Labor'),
        ('equipment', 'Equipment Rental'),
        ('subcontractor', 'Subcontractor'),
        ('utilities', 'Utilities'),
        ('office', 'Office Expenses'),
        ('travel', 'Travel'),
        ('marketing', 'Marketing'),
        ('legal', 'Legal & Professional'),
        ('insurance', 'Insurance'),
        ('permits', 'Permits & Licenses'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ]

    expense_number = models.CharField(max_length=50, unique=True)
    project = models.ForeignKey('projects.Project', on_delete=models.PROTECT, null=True, blank=True, related_name='expenses')
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, null=True, blank=True, related_name='expenses')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    
    category = models.CharField(max_length=50, choices=EXPENSE_CATEGORY_CHOICES)
    description = models.TextField()
    
    expense_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    paid_from_account = models.ForeignKey('BankAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses_paid')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    receipt_file = models.FileField(upload_to='expense_receipts/', blank=True, null=True)
    
    submitted_by = models.ForeignKey('accounts.EmployeeProfile',on_delete=models.SET_NULL,null=True,blank=True,related_name='expenses_submitted')
    approved_by = models.ForeignKey('accounts.EmployeeProfile',on_delete=models.SET_NULL,null=True,blank=True,related_name='expenses_approved')
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-expense_date']

    def __str__(self):
        return f"{self.expense_number} - {self.category} - {self.amount}"


# ==================== BANK & ACCOUNTS ====================

class BankAccount(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('savings', 'Savings Account'),
        ('current', 'Current Account'),
        ('od', 'Overdraft Account'),
        ('cc', 'Cash Credit'),
    ]

    account_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50, unique=True)
    bank_name = models.CharField(max_length=100)
    branch = models.CharField(max_length=100, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    swift_code = models.CharField(max_length=20, blank=True, null=True)
    
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    currency = models.CharField(max_length=3, default='INR')
    
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"


class BankTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('fee', 'Bank Fee'),
        ('interest', 'Interest'),
    ]

    account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name='transactions')
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='bank_transactions')
    expense = models.ForeignKey(Expense, on_delete=models.SET_NULL, null=True, blank=True, related_name='bank_transactions')
    
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-transaction_date']

    def __str__(self):
        return f"{self.account.account_number} - {self.transaction_type} - {self.amount}"


# ==================== BUDGETING ====================

class Budget(models.Model):
    BUDGET_TYPE_CHOICES = [
        ('project', 'Project Budget'),
        ('department', 'Department Budget'),
        ('annual', 'Annual Budget'),
        ('quarterly', 'Quarterly Budget'),
    ]

    name = models.CharField(max_length=200)
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPE_CHOICES)
    
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=True, blank=True, related_name='finance_budgets')
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    total_budget = models.DecimalField(max_digits=15, decimal_places=2)
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    spent_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True, null=True)
    
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='budgets_created')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.start_date} to {self.end_date}"

    @property
    def remaining_budget(self):
        return self.total_budget - self.spent_amount


class BudgetLineItem(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='line_items')
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.budget.name} - {self.category}"


# ==================== FINANCIAL REPORTING ====================

class FinancialPeriod(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class TaxConfiguration(models.Model):
    tax_name = models.CharField(max_length=100)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.tax_name} - {self.tax_rate}%"


# ==================== COST TRACKING ====================

class CostCenter(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.code} - {self.name}"


class ProjectCost(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='costs')
    cost_center = models.ForeignKey(CostCenter, on_delete=models.PROTECT, related_name='project_costs')
    
    date = models.DateField()
    description = models.CharField(max_length=255)
    
    budgeted_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    actual_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    expense = models.ForeignKey(Expense, on_delete=models.SET_NULL, null=True, blank=True, related_name='project_costs')
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.project} - {self.cost_center} - {self.actual_amount}"


# ==================== PETTY CASH ====================

class PettyCashAccount(models.Model):
    name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50, unique=True)
    custodian = models.ForeignKey(EmployeeProfile, on_delete=models.PROTECT, related_name='petty_cash_accounts')
    
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maximum_limit = models.DecimalField(max_digits=10, decimal_places=2)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.custodian}"


class PettyCashTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('withdrawal', 'Withdrawal'),
        ('reimbursement', 'Reimbursement'),
        ('replenishment', 'Replenishment'),
    ]

    account = models.ForeignKey(PettyCashAccount, on_delete=models.PROTECT, related_name='transactions')
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    
    description = models.TextField()
    receipt_number = models.CharField(max_length=50, blank=True, null=True)
    
    requested_by = models.ForeignKey(EmployeeProfile, on_delete=models.PROTECT, related_name='petty_cash_requests')
    approved_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='petty_cash_approvals')
    
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-transaction_date']

    def __str__(self):
        return f"{self.account} - {self.transaction_type} - {self.amount}"


# ==================== ASSET MANAGEMENT ====================

class Asset(models.Model):
    ASSET_TYPE_CHOICES = [
        ('land', 'Land'),
        ('building', 'Building'),
        ('vehicle', 'Vehicle'),
        ('equipment', 'Equipment'),
        ('machinery', 'Machinery'),
        ('furniture', 'Furniture'),
        ('it_equipment', 'IT Equipment'),
        ('other', 'Other'),
    ]

    asset_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    asset_type = models.CharField(max_length=50, choices=ASSET_TYPE_CHOICES)
    
    purchase_date = models.DateField()
    purchase_price = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Depreciation
    useful_life_years = models.IntegerField(default=5)
    salvage_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    depreciation_method = models.CharField(max_length=50, default='straight_line')
    accumulated_depreciation = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    current_value = models.DecimalField(max_digits=15, decimal_places=2)
    
    location = models.CharField(max_length=200, blank=True, null=True)
    assigned_to = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_assets')
    project = models.ForeignKey('projects.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    
    is_active = models.BooleanField(default=True)
    disposal_date = models.DateField(null=True, blank=True)
    disposal_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.asset_code} - {self.name}"


# ==================== COMMISSION & INCENTIVES ====================

class CommissionStructure(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    commission_type = models.CharField(max_length=50, choices=[
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('tiered', 'Tiered'),
    ])
    
    rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    applicable_to = models.CharField(max_length=50, choices=[
        ('sales', 'Sales Team'),
        ('brokers', 'Brokers'),
        ('channel_partners', 'Channel Partners'),
    ])
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Commission(models.Model):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.PROTECT, null=True, blank=True, related_name='commissions')
    broker_name = models.CharField(max_length=200, blank=True, null=True)
    
    allocation = models.ForeignKey(Allocation, on_delete=models.PROTECT, related_name='commissions')
    structure = models.ForeignKey(CommissionStructure, on_delete=models.PROTECT, related_name='commissions')
    
    base_amount = models.DecimalField(max_digits=15, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    
    payment_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Commission - {self.allocation} - {self.commission_amount}"