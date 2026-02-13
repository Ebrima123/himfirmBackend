# finance/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import (
    Invoice, InvoiceLineItem, Payment, Vendor, PurchaseOrder,
    PurchaseOrderItem, Expense, BankAccount, BankTransaction,
    Budget, BudgetLineItem, FinancialPeriod, TaxConfiguration,
    CostCenter, ProjectCost, PettyCashAccount, PettyCashTransaction,
    Asset, CommissionStructure, Commission
)


# ==================== INLINE ADMINS ====================

class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 1
    fields = ('description', 'quantity', 'unit', 'unit_price', 'tax_rate', 'discount_percentage', 'amount')
    readonly_fields = ('amount',)


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ('description', 'quantity', 'unit', 'unit_price', 'tax_rate', 'amount', 'received_quantity')
    readonly_fields = ('amount',)


class BudgetLineItemInline(admin.TabularInline):
    model = BudgetLineItem
    extra = 1
    fields = ('category', 'description', 'allocated_amount', 'spent_amount')
    readonly_fields = ('spent_amount',)


# ==================== INVOICE ADMIN ====================

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 'customer_name', 'invoice_type', 'issue_date',
        'due_date', 'amount_display', 'paid_amount_display', 'balance_display',
        'status_badge', 'project_name'
    )
    list_filter = ('status', 'invoice_type', 'issue_date', 'due_date', 'created_at')
    search_fields = (
        'invoice_number', 'customer__name', 'allocation__unit__unit_number',
        'project__name', 'notes'
    )
    readonly_fields = (
        'invoice_number', 'created_at', 'updated_at', 'created_by',
        'approved_by', 'approved_date', 'balance_due'
    )
    date_hierarchy = 'issue_date'
    inlines = [InvoiceLineItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'invoice_number', 'invoice_type', 'allocation', 'project', 'customer'
            )
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date')
        }),
        ('Financial Details', {
            'fields': (
                'subtotal', 'tax_amount', 'discount_amount', 'amount',
                'paid_amount', 'retention_percentage', 'retention_amount'
            )
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes', 'terms_and_conditions')
        }),
        ('Approval & Tracking', {
            'fields': (
                'created_by', 'created_at', 'approved_by', 'approved_date', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def customer_name(self, obj):
        return obj.customer.name if obj.customer else '-'
    customer_name.short_description = 'Customer'
    customer_name.admin_order_field = 'customer__name'
    
    def project_name(self, obj):
        return obj.project.name if obj.project else '-'
    project_name.short_description = 'Project'
    
    def amount_display(self, obj):
        return f"₹{obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def paid_amount_display(self, obj):
        return f"₹{obj.paid_amount:,.2f}"
    paid_amount_display.short_description = 'Paid'
    
    def balance_display(self, obj):
        balance = obj.balance_due
        color = 'green' if balance == 0 else 'red'
        return format_html(
            '<span style="color: {};">₹{:,.2f}</span>',
            color, balance
        )
    balance_display.short_description = 'Balance'
    
    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'pending_approval': 'orange',
            'approved': 'blue',
            'sent': 'cyan',
            'unpaid': 'red',
            'partial': 'orange',
            'paid': 'green',
            'overdue': 'darkred',
            'cancelled': 'gray',
            'void': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new invoice
            obj.created_by = request.user.profile
        super().save_model(request, obj, form, change)


# ==================== PAYMENT ADMIN ====================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'receipt_number', 'customer_name', 'invoice_number', 'amount_display',
        'payment_date', 'payment_method', 'status_badge', 'received_by_name'
    )
    list_filter = ('status', 'payment_method', 'payment_date', 'created_at')
    search_fields = (
        'receipt_number', 'customer__name', 'invoice__invoice_number',
        'reference_number', 'bank_name'
    )
    readonly_fields = ('receipt_number', 'created_at', 'updated_at', 'received_by')
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'receipt_number', 'customer', 'invoice', 'amount', 'payment_date'
            )
        }),
        ('Payment Details', {
            'fields': (
                'payment_method', 'reference_number', 'bank_name', 'cheque_date'
            )
        }),
        ('Banking', {
            'fields': ('deposited_to_account', 'status')
        }),
        ('Additional Info', {
            'fields': ('notes', 'received_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def customer_name(self, obj):
        return obj.customer.name
    customer_name.short_description = 'Customer'
    customer_name.admin_order_field = 'customer__name'
    
    def invoice_number(self, obj):
        return obj.invoice.invoice_number if obj.invoice else '-'
    invoice_number.short_description = 'Invoice'
    
    def amount_display(self, obj):
        return f"₹{obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def received_by_name(self, obj):
        return obj.received_by if obj.received_by else '-'
    received_by_name.short_description = 'Received By'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'cleared': 'green',
            'bounced': 'red',
            'cancelled': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.received_by = request.user.profile
        super().save_model(request, obj, form, change)


# ==================== VENDOR ADMIN ====================

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = (
        'vendor_code', 'name', 'vendor_type', 'contact_person',
        'email', 'phone', 'credit_limit_display', 'is_active'
    )
    list_filter = ('vendor_type', 'is_active', 'created_at')
    search_fields = ('vendor_code', 'name', 'contact_person', 'email', 'gst_number', 'pan_number')
    readonly_fields = ('vendor_code', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('vendor_code', 'name', 'vendor_type')
        }),
        ('Contact Details', {
            'fields': ('contact_person', 'email', 'phone', 'address')
        }),
        ('Tax Information', {
            'fields': ('pan_number', 'gst_number', 'tax_id')
        }),
        ('Banking Details', {
            'fields': ('bank_account_number', 'bank_name', 'ifsc_code')
        }),
        ('Credit Terms', {
            'fields': ('credit_limit', 'payment_terms_days', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def credit_limit_display(self, obj):
        return f"₹{obj.credit_limit:,.2f}"
    credit_limit_display.short_description = 'Credit Limit'


# ==================== PURCHASE ORDER ADMIN ====================

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        'po_number', 'vendor_name', 'po_date', 'delivery_date',
        'total_amount_display', 'status_badge', 'project_name'
    )
    list_filter = ('status', 'po_date', 'delivery_date', 'created_at')
    search_fields = ('po_number', 'vendor__name', 'project__name')
    readonly_fields = ('po_number', 'created_at', 'updated_at', 'created_by', 'approved_by')
    date_hierarchy = 'po_date'
    inlines = [PurchaseOrderItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('po_number', 'vendor', 'project', 'po_date', 'delivery_date')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax_amount', 'total_amount')
        }),
        ('Delivery & Terms', {
            'fields': ('delivery_address', 'terms_and_conditions', 'notes')
        }),
        ('Status & Approval', {
            'fields': ('status', 'created_by', 'approved_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def vendor_name(self, obj):
        return obj.vendor.name
    vendor_name.short_description = 'Vendor'
    vendor_name.admin_order_field = 'vendor__name'
    
    def project_name(self, obj):
        return obj.project.name if obj.project else '-'
    project_name.short_description = 'Project'
    
    def total_amount_display(self, obj):
        return f"₹{obj.total_amount:,.2f}"
    total_amount_display.short_description = 'Total Amount'
    
    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'pending_approval': 'orange',
            'approved': 'blue',
            'sent': 'cyan',
            'partial': 'orange',
            'received': 'green',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user.profile
        super().save_model(request, obj, form, change)


# ==================== EXPENSE ADMIN ====================

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        'expense_number', 'category', 'vendor_name', 'expense_date',
        'total_amount_display', 'status_badge', 'submitted_by_name', 'project_name'
    )
    list_filter = ('status', 'category', 'expense_date', 'created_at')
    search_fields = (
        'expense_number', 'vendor__name', 'description', 'project__name'
    )
    readonly_fields = ('expense_number', 'created_at', 'updated_at', 'submitted_by', 'approved_by')
    date_hierarchy = 'expense_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('expense_number', 'category', 'expense_date', 'project', 'vendor', 'purchase_order')
        }),
        ('Details', {
            'fields': ('description', 'amount', 'tax_amount', 'total_amount')
        }),
        ('Payment', {
            'fields': ('payment_method', 'paid_from_account')
        }),
        ('Attachment & Notes', {
            'fields': ('receipt_file', 'notes')
        }),
        ('Approval', {
            'fields': ('status', 'submitted_by', 'approved_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def vendor_name(self, obj):
        return obj.vendor.name if obj.vendor else '-'
    vendor_name.short_description = 'Vendor'
    
    def project_name(self, obj):
        return obj.project.name if obj.project else '-'
    project_name.short_description = 'Project'
    
    def total_amount_display(self, obj):
        return f"₹{obj.total_amount:,.2f}"
    total_amount_display.short_description = 'Total Amount'
    
    def submitted_by_name(self, obj):
        return obj.submitted_by if obj.submitted_by else '-'
    submitted_by_name.short_description = 'Submitted By'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'blue',
            'paid': 'green',
            'rejected': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.submitted_by = request.user.profile
        super().save_model(request, obj, form, change)


# ==================== BANK ACCOUNT ADMIN ====================

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        'account_name', 'account_number', 'bank_name', 'account_type',
        'current_balance_display', 'is_active', 'is_primary'
    )
    list_filter = ('account_type', 'is_active', 'is_primary', 'created_at')
    search_fields = ('account_name', 'account_number', 'bank_name', 'ifsc_code')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Account Information', {
            'fields': ('account_name', 'account_number', 'bank_name', 'branch', 'account_type')
        }),
        ('Banking Details', {
            'fields': ('ifsc_code', 'swift_code', 'currency')
        }),
        ('Balance', {
            'fields': ('opening_balance', 'current_balance')
        }),
        ('Status', {
            'fields': ('is_active', 'is_primary')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def current_balance_display(self, obj):
        color = 'green' if obj.current_balance >= 0 else 'red'
        return format_html(
            '<span style="color: {};">₹{:,.2f}</span>',
            color, obj.current_balance
        )
    current_balance_display.short_description = 'Current Balance'


@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'account_name', 'transaction_date', 'transaction_type',
        'amount_display', 'balance_after_display', 'reference_number'
    )
    list_filter = ('transaction_type', 'transaction_date', 'account')
    search_fields = ('reference_number', 'description', 'account__account_number')
    readonly_fields = ('created_at',)
    date_hierarchy = 'transaction_date'
    
    def account_name(self, obj):
        return obj.account.account_name
    account_name.short_description = 'Account'
    
    def amount_display(self, obj):
        color = 'green' if obj.transaction_type == 'deposit' else 'red'
        return format_html(
            '<span style="color: {};">₹{:,.2f}</span>',
            color, obj.amount
        )
    amount_display.short_description = 'Amount'
    
    def balance_after_display(self, obj):
        return f"₹{obj.balance_after:,.2f}"
    balance_after_display.short_description = 'Balance After'


# ==================== BUDGET ADMIN ====================

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'budget_type', 'project_name', 'start_date', 'end_date',
        'total_budget_display', 'spent_amount_display', 'remaining_display'
    )
    list_filter = ('budget_type', 'start_date', 'end_date', 'created_at')
    search_fields = ('name', 'project__name')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'remaining_budget')
    date_hierarchy = 'start_date'
    inlines = [BudgetLineItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'budget_type', 'project')
        }),
        ('Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Budget Amounts', {
            'fields': ('total_budget', 'allocated_amount', 'spent_amount', 'remaining_budget')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Tracking', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def project_name(self, obj):
        return obj.project.name if obj.project else '-'
    project_name.short_description = 'Project'
    
    def total_budget_display(self, obj):
        return f"₹{obj.total_budget:,.2f}"
    total_budget_display.short_description = 'Total Budget'
    
    def spent_amount_display(self, obj):
        return f"₹{obj.spent_amount:,.2f}"
    spent_amount_display.short_description = 'Spent'
    
    def remaining_display(self, obj):
        remaining = obj.remaining_budget
        color = 'green' if remaining > 0 else 'red'
        return format_html(
            '<span style="color: {};">₹{:,.2f}</span>',
            color, remaining
        )
    remaining_display.short_description = 'Remaining'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user.employeeprofile
        super().save_model(request, obj, form, change)


# ==================== OTHER ADMINS ====================

@admin.register(FinancialPeriod)
class FinancialPeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_closed')
    list_filter = ('is_closed', 'start_date')
    search_fields = ('name',)
    readonly_fields = ('created_at',)


@admin.register(TaxConfiguration)
class TaxConfigurationAdmin(admin.ModelAdmin):
    list_display = ('tax_name', 'tax_rate', 'is_active', 'effective_from', 'effective_to')
    list_filter = ('is_active', 'effective_from')
    search_fields = ('tax_name',)
    readonly_fields = ('created_at',)


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'parent', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at',)


@admin.register(ProjectCost)
class ProjectCostAdmin(admin.ModelAdmin):
    list_display = (
        'project', 'cost_center', 'date', 'budgeted_amount_display',
        'actual_amount_display', 'variance_display'
    )
    list_filter = ('date', 'project', 'cost_center')
    search_fields = ('project__name', 'description')
    readonly_fields = ('created_at',)
    date_hierarchy = 'date'
    
    def budgeted_amount_display(self, obj):
        return f"₹{obj.budgeted_amount:,.2f}"
    budgeted_amount_display.short_description = 'Budgeted'
    
    def actual_amount_display(self, obj):
        return f"₹{obj.actual_amount:,.2f}"
    actual_amount_display.short_description = 'Actual'
    
    def variance_display(self, obj):
        variance = obj.budgeted_amount - obj.actual_amount
        color = 'green' if variance >= 0 else 'red'
        return format_html(
            '<span style="color: {};">₹{:,.2f}</span>',
            color, variance
        )
    variance_display.short_description = 'Variance'


@admin.register(PettyCashAccount)
class PettyCashAccountAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'account_number', 'custodian', 'current_balance_display',
        'maximum_limit_display', 'is_active'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'account_number', 'custodian__user__username')
    readonly_fields = ('created_at', 'updated_at')
    
    def current_balance_display(self, obj):
        return f"₹{obj.current_balance:,.2f}"
    current_balance_display.short_description = 'Current Balance'
    
    def maximum_limit_display(self, obj):
        return f"₹{obj.maximum_limit:,.2f}"
    maximum_limit_display.short_description = 'Max Limit'


@admin.register(PettyCashTransaction)
class PettyCashTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'account', 'transaction_date', 'transaction_type', 'amount_display',
        'requested_by', 'approved_by'
    )
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('description', 'receipt_number')
    readonly_fields = ('created_at',)
    date_hierarchy = 'transaction_date'
    
    def amount_display(self, obj):
        return f"₹{obj.amount:,.2f}"
    amount_display.short_description = 'Amount'


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        'asset_code', 'name', 'asset_type', 'purchase_date',
        'purchase_price_display', 'current_value_display', 'is_active', 'assigned_to'
    )
    list_filter = ('asset_type', 'is_active', 'purchase_date')
    search_fields = ('asset_code', 'name', 'location')
    readonly_fields = ('asset_code', 'created_at', 'updated_at')
    date_hierarchy = 'purchase_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('asset_code', 'name', 'asset_type', 'purchase_date', 'purchase_price')
        }),
        ('Depreciation', {
            'fields': (
                'useful_life_years', 'salvage_value', 'depreciation_method',
                'accumulated_depreciation', 'current_value'
            )
        }),
        ('Assignment', {
            'fields': ('location', 'assigned_to', 'project')
        }),
        ('Disposal', {
            'fields': ('is_active', 'disposal_date', 'disposal_value'),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def purchase_price_display(self, obj):
        return f"₹{obj.purchase_price:,.2f}"
    purchase_price_display.short_description = 'Purchase Price'
    
    def current_value_display(self, obj):
        return f"₹{obj.current_value:,.2f}"
    current_value_display.short_description = 'Current Value'


@admin.register(CommissionStructure)
class CommissionStructureAdmin(admin.ModelAdmin):
    list_display = ('name', 'commission_type', 'rate', 'applicable_to', 'is_active')
    list_filter = ('commission_type', 'applicable_to', 'is_active')
    search_fields = ('name',)
    readonly_fields = ('created_at',)


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = (
        'allocation', 'employee_or_broker', 'base_amount_display',
        'commission_amount_display', 'status_badge', 'payment_date'
    )
    list_filter = ('status', 'payment_date', 'created_at')
    search_fields = ('employee__user__username', 'broker_name', 'allocation__unit__unit_number')
    readonly_fields = ('created_at',)
    
    def employee_or_broker(self, obj):
        return obj.employee if obj.employee else obj.broker_name
    employee_or_broker.short_description = 'Employee/Broker'
    
    def base_amount_display(self, obj):
        return f"₹{obj.base_amount:,.2f}"
    base_amount_display.short_description = 'Base Amount'
    
    def commission_amount_display(self, obj):
        return f"₹{obj.commission_amount:,.2f}"
    commission_amount_display.short_description = 'Commission'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'blue',
            'paid': 'green',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'