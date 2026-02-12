# finance/serializers.py
from rest_framework import serializers
from decimal import Decimal
from .models import (
    Invoice, InvoiceLineItem, Payment, Vendor, PurchaseOrder, 
    PurchaseOrderItem, Expense, BankAccount, BankTransaction,
    Budget, BudgetLineItem, FinancialPeriod, TaxConfiguration,
    CostCenter, ProjectCost, PettyCashAccount, PettyCashTransaction,
    Asset, CommissionStructure, Commission
)


# ==================== INVOICING SERIALIZERS ====================

class InvoiceLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLineItem
        fields = [
            'id', 'invoice', 'description', 'quantity', 'unit', 
            'unit_price', 'tax_rate', 'discount_percentage', 'amount'
        ]
    
    def validate(self, data):
        # Calculate amount
        quantity = data.get('quantity', 1)
        unit_price = data.get('unit_price', 0)
        tax_rate = data.get('tax_rate', 0)
        discount_percentage = data.get('discount_percentage', 0)
        
        subtotal = quantity * unit_price
        discount = subtotal * (discount_percentage / 100)
        taxable = subtotal - discount
        tax = taxable * (tax_rate / 100)
        
        data['amount'] = taxable + tax
        
        return data


class InvoiceSerializer(serializers.ModelSerializer):
    allocation_name = serializers.CharField(source='allocation.__str__', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.__str__', read_only=True)
    balance_due = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'invoice_type', 'issue_date', 'due_date',
            'allocation', 'allocation_name',
            'project', 'project_name',
            'customer', 'customer_name',
            'subtotal', 'tax_amount', 'discount_amount', 'amount', 'paid_amount',
            'retention_percentage', 'retention_amount',
            'status', 'notes', 'terms_and_conditions',
            'created_by', 'created_by_name',
            'approved_by', 'approved_date',
            'balance_due',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['invoice_number', 'created_by', 'approved_by', 'approved_date', 'created_at', 'updated_at']


class InvoiceDetailSerializer(InvoiceSerializer):
    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    payments = serializers.SerializerMethodField()
    
    class Meta(InvoiceSerializer.Meta):
        fields = InvoiceSerializer.Meta.fields + ['line_items', 'payments']
    
    def get_payments(self, obj):
        payments = obj.payments.all()
        return PaymentSerializer(payments, many=True).data


# ==================== PAYMENT SERIALIZERS ====================

class PaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    received_by_name = serializers.CharField(source='received_by.__str__', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    account_name = serializers.CharField(source='deposited_to_account.account_name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'receipt_number', 'payment_date', 'amount', 'payment_method',
            'customer', 'customer_name',
            'invoice', 'invoice_number',
            'reference_number', 'bank_name', 'cheque_date',
            'status',
            'received_by', 'received_by_name',
            'deposited_to_account', 'account_name',
            'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['receipt_number', 'received_by', 'created_at', 'updated_at']


class PaymentDetailSerializer(PaymentSerializer):
    invoice_details = InvoiceSerializer(source='invoice', read_only=True)
    
    class Meta(PaymentSerializer.Meta):
        fields = PaymentSerializer.Meta.fields + ['invoice_details']


# ==================== VENDOR SERIALIZERS ====================

class VendorSerializer(serializers.ModelSerializer):
    outstanding_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'vendor_code', 'name', 'vendor_type',
            'contact_person', 'email', 'phone', 'address',
            'pan_number', 'gst_number', 'tax_id',
            'bank_account_number', 'bank_name', 'ifsc_code',
            'credit_limit', 'payment_terms_days',
            'is_active',
            'outstanding_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['vendor_code', 'created_at', 'updated_at']


# ==================== PURCHASE ORDER SERIALIZERS ====================

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    remaining_quantity = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'purchase_order', 'description', 'quantity', 'unit',
            'unit_price', 'tax_rate', 'amount', 'received_quantity',
            'remaining_quantity'
        ]
    
    def get_remaining_quantity(self, obj):
        return obj.quantity - obj.received_quantity
    
    def validate(self, data):
        # Calculate amount
        quantity = data.get('quantity', 1)
        unit_price = data.get('unit_price', 0)
        tax_rate = data.get('tax_rate', 0)
        
        subtotal = quantity * unit_price
        tax = subtotal * (tax_rate / 100)
        
        data['amount'] = subtotal + tax
        
        return data


class PurchaseOrderSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.__str__', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'po_date', 'delivery_date',
            'vendor', 'vendor_name',
            'project', 'project_name',
            'subtotal', 'tax_amount', 'total_amount',
            'status',
            'delivery_address', 'terms_and_conditions', 'notes',
            'created_by', 'created_by_name',
            'approved_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['po_number', 'created_by', 'approved_by', 'created_at', 'updated_at']


class PurchaseOrderDetailSerializer(PurchaseOrderSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    vendor_details = VendorSerializer(source='vendor', read_only=True)
    
    class Meta(PurchaseOrderSerializer.Meta):
        fields = PurchaseOrderSerializer.Meta.fields + ['items', 'vendor_details']


# ==================== EXPENSE SERIALIZERS ====================

class ExpenseSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    po_number = serializers.CharField(source='purchase_order.po_number', read_only=True)
    # submitted_by_name = serializers.CharField(source='submitted_by.__str__', read_only=True)
    # approved_by_name = serializers.CharField(source='approved_by.__str__', read_only=True)
    account_name = serializers.CharField(source='paid_from_account.account_name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'expense_number', 'expense_date', 'category', 'category_display',
            'project', 'project_name',
            'vendor', 'vendor_name',
            'purchase_order', 'po_number',
            'description', 'amount', 'tax_amount', 'total_amount',
            'payment_method',
            'paid_from_account', 'account_name',
            'status', 'status_display',
            'receipt_file',
            'submitted_by', 'submitted_by_name',
            'approved_by', 'approved_by_name',
            'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['expense_number', 'submitted_by', 'approved_by', 'created_at', 'updated_at']
    
    def validate(self, data):
        # Calculate total amount if not provided
        if 'total_amount' not in data:
            amount = data.get('amount', 0)
            tax_amount = data.get('tax_amount', 0)
            data['total_amount'] = amount + tax_amount
        
        return data


class ExpenseDetailSerializer(ExpenseSerializer):
    vendor_details = VendorSerializer(source='vendor', read_only=True)
    po_details = PurchaseOrderSerializer(source='purchase_order', read_only=True)
    
    class Meta(ExpenseSerializer.Meta):
        fields = ExpenseSerializer.Meta.fields + ['vendor_details', 'po_details']


# ==================== BANK ACCOUNT SERIALIZERS ====================

class BankAccountSerializer(serializers.ModelSerializer):
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    available_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = BankAccount
        fields = [
            'id', 'account_name', 'account_number', 'bank_name', 'branch',
            'ifsc_code', 'swift_code',
            'account_type', 'account_type_display',
            'currency',
            'opening_balance', 'current_balance', 'available_balance',
            'is_active', 'is_primary',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['current_balance', 'created_at', 'updated_at']
    
    def get_available_balance(self, obj):
        # Could include logic for pending transactions
        return obj.current_balance


class BankTransactionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.account_name', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    payment_receipt = serializers.CharField(source='payment.receipt_number', read_only=True)
    expense_number = serializers.CharField(source='expense.expense_number', read_only=True)
    
    class Meta:
        model = BankTransaction
        fields = [
            'id', 'account', 'account_name',
            'transaction_date', 'transaction_type', 'transaction_type_display',
            'amount', 'balance_after',
            'reference_number', 'description',
            'payment', 'payment_receipt',
            'expense', 'expense_number',
            'created_at'
        ]
        read_only_fields = ['balance_after', 'created_at']


# ==================== BUDGET SERIALIZERS ====================

class BudgetLineItemSerializer(serializers.ModelSerializer):
    remaining_amount = serializers.SerializerMethodField()
    utilization_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = BudgetLineItem
        fields = [
            'id', 'budget', 'category', 'description',
            'allocated_amount', 'spent_amount',
            'remaining_amount', 'utilization_percentage'
        ]
    
    def get_remaining_amount(self, obj):
        return obj.allocated_amount - obj.spent_amount
    
    def get_utilization_percentage(self, obj):
        if obj.allocated_amount > 0:
            return round((obj.spent_amount / obj.allocated_amount) * 100, 2)
        return 0


class BudgetSerializer(serializers.ModelSerializer):
    budget_type_display = serializers.CharField(source='get_budget_type_display', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.__str__', read_only=True)
    remaining_budget = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    utilization_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Budget
        fields = [
            'id', 'name', 'budget_type', 'budget_type_display',
            'project', 'project_name',
            'start_date', 'end_date',
            'total_budget', 'allocated_amount', 'spent_amount',
            'remaining_budget', 'utilization_percentage',
            'notes',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_utilization_percentage(self, obj):
        if obj.total_budget > 0:
            return round((obj.spent_amount / obj.total_budget) * 100, 2)
        return 0


class BudgetDetailSerializer(BudgetSerializer):
    line_items = BudgetLineItemSerializer(many=True, read_only=True)
    
    class Meta(BudgetSerializer.Meta):
        fields = BudgetSerializer.Meta.fields + ['line_items']


# ==================== FINANCIAL PERIOD SERIALIZERS ====================

class FinancialPeriodSerializer(serializers.ModelSerializer):
    duration_days = serializers.SerializerMethodField()
    
    class Meta:
        model = FinancialPeriod
        fields = [
            'id', 'name', 'start_date', 'end_date',
            'is_closed', 'duration_days',
            'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_duration_days(self, obj):
        return (obj.end_date - obj.start_date).days


class TaxConfigurationSerializer(serializers.ModelSerializer):
    is_currently_active = serializers.SerializerMethodField()
    
    class Meta:
        model = TaxConfiguration
        fields = [
            'id', 'tax_name', 'tax_rate',
            'is_active', 'is_currently_active',
            'effective_from', 'effective_to',
            'description',
            'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_is_currently_active(self, obj):
        from django.utils import timezone
        today = timezone.now().date()
        
        if not obj.is_active:
            return False
        
        if obj.effective_from > today:
            return False
        
        if obj.effective_to and obj.effective_to < today:
            return False
        
        return True


# ==================== COST TRACKING SERIALIZERS ====================

class CostCenterSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    has_children = serializers.SerializerMethodField()
    
    class Meta:
        model = CostCenter
        fields = [
            'id', 'code', 'name', 'description',
            'parent', 'parent_name',
            'has_children',
            'is_active',
            'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_has_children(self, obj):
        return obj.children.exists()


class ProjectCostSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    cost_center_name = serializers.CharField(source='cost_center.name', read_only=True)
    expense_number = serializers.CharField(source='expense.expense_number', read_only=True)
    variance = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectCost
        fields = [
            'id', 'project', 'project_name',
            'cost_center', 'cost_center_name',
            'date', 'description',
            'budgeted_amount', 'actual_amount', 'variance',
            'expense', 'expense_number',
            'notes',
            'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_variance(self, obj):
        return obj.budgeted_amount - obj.actual_amount


# ==================== PETTY CASH SERIALIZERS ====================

class PettyCashAccountSerializer(serializers.ModelSerializer):
    custodian_name = serializers.CharField(source='custodian.__str__', read_only=True)
    available_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = PettyCashAccount
        fields = [
            'id', 'name', 'account_number',
            'custodian', 'custodian_name',
            'opening_balance', 'current_balance', 'maximum_limit',
            'available_amount',
            'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['current_balance', 'created_at', 'updated_at']
    
    def get_available_amount(self, obj):
        return obj.maximum_limit - obj.current_balance


class PettyCashTransactionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.__str__', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.__str__', read_only=True)
    
    class Meta:
        model = PettyCashTransaction
        fields = [
            'id', 'account', 'account_name',
            'transaction_date', 'transaction_type', 'transaction_type_display',
            'amount', 'balance_after',
            'description', 'receipt_number',
            'requested_by', 'requested_by_name',
            'approved_by', 'approved_by_name',
            'created_at'
        ]
        read_only_fields = ['balance_after', 'created_at']


# ==================== ASSET SERIALIZERS ====================

class AssetSerializer(serializers.ModelSerializer):
    asset_type_display = serializers.CharField(source='get_asset_type_display', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.__str__', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    age_years = serializers.SerializerMethodField()
    depreciation_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Asset
        fields = [
            'id', 'asset_code', 'name', 'asset_type', 'asset_type_display',
            'purchase_date', 'purchase_price',
            'useful_life_years', 'salvage_value', 'depreciation_method',
            'accumulated_depreciation', 'current_value',
            'age_years', 'depreciation_rate',
            'location',
            'assigned_to', 'assigned_to_name',
            'project', 'project_name',
            'is_active', 'disposal_date', 'disposal_value',
            'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['asset_code', 'accumulated_depreciation', 'current_value', 'created_at', 'updated_at']
    
    def get_age_years(self, obj):
        from django.utils import timezone
        age_days = (timezone.now().date() - obj.purchase_date).days
        return round(age_days / 365.25, 2)
    
    def get_depreciation_rate(self, obj):
        if obj.useful_life_years > 0:
            return round(100 / obj.useful_life_years, 2)
        return 0


# ==================== COMMISSION SERIALIZERS ====================

class CommissionStructureSerializer(serializers.ModelSerializer):
    commission_type_display = serializers.CharField(source='get_commission_type_display', read_only=True)
    applicable_to_display = serializers.CharField(source='get_applicable_to_display', read_only=True)
    
    class Meta:
        model = CommissionStructure
        fields = [
            'id', 'name', 'description',
            'commission_type', 'commission_type_display',
            'rate',
            'applicable_to', 'applicable_to_display',
            'is_active',
            'created_at'
        ]
        read_only_fields = ['created_at']


class CommissionSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.__str__', read_only=True)
    allocation_details = serializers.CharField(source='allocation.__str__', read_only=True)
    structure_name = serializers.CharField(source='structure.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Commission
        fields = [
            'id', 'employee', 'employee_name',
            'broker_name',
            'allocation', 'allocation_details',
            'structure', 'structure_name',
            'base_amount', 'commission_amount',
            'status', 'status_display',
            'payment_date',
            'notes',
            'created_at'
        ]
        read_only_fields = ['created_at']
    
    def validate(self, data):
        # Either employee or broker_name must be provided
        if not data.get('employee') and not data.get('broker_name'):
            raise serializers.ValidationError(
                "Either employee or broker_name must be provided"
            )
        
        # Calculate commission based on structure
        if 'structure' in data and 'base_amount' in data:
            structure = data['structure']
            base_amount = data['base_amount']
            
            if structure.commission_type == 'percentage':
                commission = base_amount * (structure.rate / 100)
            elif structure.commission_type == 'fixed':
                commission = structure.rate
            else:  # tiered - simplified, you can add complex logic
                commission = base_amount * (structure.rate / 100)
            
            data['commission_amount'] = commission
        
        return data


# ==================== SUMMARY SERIALIZERS ====================

class FinancialDashboardSerializer(serializers.Serializer):
    """Serializer for financial dashboard summary"""
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    net_profit = serializers.DecimalField(max_digits=15, decimal_places=2)
    outstanding_receivables = serializers.DecimalField(max_digits=15, decimal_places=2)
    outstanding_payables = serializers.DecimalField(max_digits=15, decimal_places=2)
    cash_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    period_start = serializers.DateField()
    period_end = serializers.DateField()


class ExpenseSummarySerializer(serializers.Serializer):
    """Serializer for expense summary by category"""
    category = serializers.CharField()
    category_display = serializers.CharField()
    total = serializers.DecimalField(max_digits=15, decimal_places=2)
    count = serializers.IntegerField()


class RevenueSummarySerializer(serializers.Serializer):
    """Serializer for revenue summary"""
    period = serializers.CharField()
    total_invoiced = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_collected = serializers.DecimalField(max_digits=15, decimal_places=2)
    outstanding = serializers.DecimalField(max_digits=15, decimal_places=2)