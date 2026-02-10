# finance/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InvoiceViewSet, InvoiceLineItemViewSet, PaymentViewSet,
    VendorViewSet, PurchaseOrderViewSet, PurchaseOrderItemViewSet,
    ExpenseViewSet, BankAccountViewSet, BankTransactionViewSet,
    BudgetViewSet, BudgetLineItemViewSet, FinancialPeriodViewSet,
    TaxConfigurationViewSet, CostCenterViewSet, ProjectCostViewSet,
    PettyCashAccountViewSet, PettyCashTransactionViewSet,
    AssetViewSet, CommissionStructureViewSet, CommissionViewSet
)

app_name = 'finance'

router = DefaultRouter()

# Invoicing & Billing
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'invoice-line-items', InvoiceLineItemViewSet, basename='invoice-line-item')
router.register(r'payments', PaymentViewSet, basename='payment')

# Vendor Management
router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'purchase-order-items', PurchaseOrderItemViewSet, basename='purchase-order-item')

# Expenses
router.register(r'expenses', ExpenseViewSet, basename='expense')

# Banking
router.register(r'bank-accounts', BankAccountViewSet, basename='bank-account')
router.register(r'bank-transactions', BankTransactionViewSet, basename='bank-transaction')

# Budgeting
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'budget-line-items', BudgetLineItemViewSet, basename='budget-line-item')

# Cost Tracking
router.register(r'cost-centers', CostCenterViewSet, basename='cost-center')
router.register(r'project-costs', ProjectCostViewSet, basename='project-cost')

# Financial Periods & Tax
router.register(r'financial-periods', FinancialPeriodViewSet, basename='financial-period')
router.register(r'tax-configurations', TaxConfigurationViewSet, basename='tax-configuration')

# Petty Cash
router.register(r'petty-cash-accounts', PettyCashAccountViewSet, basename='petty-cash-account')
router.register(r'petty-cash-transactions', PettyCashTransactionViewSet, basename='petty-cash-transaction')

# Assets
router.register(r'assets', AssetViewSet, basename='asset')

# Commissions
router.register(r'commission-structures', CommissionStructureViewSet, basename='commission-structure')
router.register(r'commissions', CommissionViewSet, basename='commission')

urlpatterns = [
    path('', include(router.urls)),
]