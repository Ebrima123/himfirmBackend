# finance/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q, F, Count
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    Invoice, InvoiceLineItem, Payment, Vendor, PurchaseOrder, 
    PurchaseOrderItem, Expense, BankAccount, BankTransaction,
    Budget, BudgetLineItem, FinancialPeriod, TaxConfiguration,
    CostCenter, ProjectCost, PettyCashAccount, PettyCashTransaction,
    Asset, CommissionStructure, Commission
)
from .serializers import (
    InvoiceSerializer, InvoiceDetailSerializer, InvoiceLineItemSerializer,
    PaymentSerializer, PaymentDetailSerializer, VendorSerializer,
    PurchaseOrderSerializer, PurchaseOrderDetailSerializer, PurchaseOrderItemSerializer,
    ExpenseSerializer, ExpenseDetailSerializer, BankAccountSerializer,
    BankTransactionSerializer, BudgetSerializer, BudgetDetailSerializer,
    BudgetLineItemSerializer, FinancialPeriodSerializer, TaxConfigurationSerializer,
    CostCenterSerializer, ProjectCostSerializer, PettyCashAccountSerializer,
    PettyCashTransactionSerializer, AssetSerializer, CommissionStructureSerializer,
    CommissionSerializer
)
from .permissions import IsFinanceManager, IsAccountant, CanApproveExpenses
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters


# ==================== INVOICING ====================

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().select_related(
        'allocation', 'project', 'customer', 'created_by', 'approved_by'
    ).prefetch_related('line_items', 'payments')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'invoice_type', 'customer', 'project']
    search_fields = ['invoice_number', 'customer__name']
    ordering_fields = ['issue_date', 'due_date', 'amount', 'created_at']
    ordering = ['-issue_date']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InvoiceDetailSerializer
        return InvoiceSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.profile)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an invoice"""
        invoice = self.get_object()
        
        if invoice.status != 'pending_approval':
            return Response(
                {'error': 'Only pending invoices can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invoice.status = 'approved'
        invoice.approved_by = request.user.profile
        invoice.approved_date = timezone.now()
        invoice.save()
        
        return Response({'status': 'Invoice approved'})

    @action(detail=True, methods=['post'])
    def send_to_customer(self, request, pk=None):
        """Mark invoice as sent"""
        invoice = self.get_object()
        
        if invoice.status not in ['approved', 'draft']:
            return Response(
                {'error': 'Invoice must be approved or draft to send'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invoice.status = 'sent'
        invoice.save()
        
        # Here you can add email sending logic
        
        return Response({'status': 'Invoice sent to customer'})

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark invoice as fully paid"""
        invoice = self.get_object()
        
        if invoice.paid_amount >= invoice.amount:
            invoice.status = 'paid'
            invoice.save()
            return Response({'status': 'Invoice marked as paid'})
        else:
            return Response(
                {'error': f'Invoice not fully paid. Balance: {invoice.balance_due}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get all overdue invoices"""
        today = timezone.now().date()
        overdue_invoices = self.queryset.filter(
            due_date__lt=today,
            status__in=['unpaid', 'partial', 'sent']
        )
        serializer = self.get_serializer(overdue_invoices, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get invoice dashboard statistics"""
        total_outstanding = self.queryset.filter(
            status__in=['unpaid', 'partial', 'sent']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_paid_this_month = self.queryset.filter(
            status='paid',
            issue_date__month=timezone.now().month,
            issue_date__year=timezone.now().year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        overdue_count = self.queryset.filter(
            due_date__lt=timezone.now().date(),
            status__in=['unpaid', 'partial', 'sent']
        ).count()
        
        return Response({
            'total_outstanding': total_outstanding,
            'total_paid_this_month': total_paid_this_month,
            'overdue_count': overdue_count,
            'total_invoices': self.queryset.count()
        })


class InvoiceLineItemViewSet(viewsets.ModelViewSet):
    queryset = InvoiceLineItem.objects.all()
    serializer_class = InvoiceLineItemSerializer
    permission_classes = [IsAuthenticated]


# ==================== PAYMENTS ====================

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().select_related(
        'invoice', 'customer', 'received_by', 'deposited_to_account'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'customer', 'invoice']
    search_fields = ['receipt_number', 'reference_number', 'customer__name']
    ordering_fields = ['payment_date', 'amount', 'created_at']
    ordering = ['-payment_date']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaymentDetailSerializer
        return PaymentSerializer

    def perform_create(self, serializer):
        payment = serializer.save(submitted_by=self.request.user.profile)
        
        # Update invoice paid amount if linked
        if payment.invoice:
            invoice = payment.invoice
            invoice.paid_amount += payment.amount
            
            # Update invoice status
            if invoice.paid_amount >= invoice.amount:
                invoice.status = 'paid'
            elif invoice.paid_amount > 0:
                invoice.status = 'partial'
            
            invoice.save()
        
        # Create bank transaction if account specified
        if payment.deposited_to_account and payment.status == 'cleared':
            BankTransaction.objects.create(
                account=payment.deposited_to_account,
                transaction_date=payment.payment_date,
                transaction_type='deposit',
                amount=payment.amount,
                balance_after=payment.deposited_to_account.current_balance + payment.amount,
                reference_number=payment.receipt_number,
                description=f"Payment received - {payment.receipt_number}",
                payment=payment
            )
            
            # Update bank account balance
            payment.deposited_to_account.current_balance += payment.amount
            payment.deposited_to_account.save()

    @action(detail=True, methods=['post'])
    def mark_bounced(self, request, pk=None):
        """Mark payment as bounced"""
        payment = self.get_object()
        
        if payment.status != 'cleared':
            return Response(
                {'error': 'Only cleared payments can be marked as bounced'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.status = 'bounced'
        payment.save()
        
        # Reverse invoice payment
        if payment.invoice:
            invoice = payment.invoice
            invoice.paid_amount -= payment.amount
            
            if invoice.paid_amount <= 0:
                invoice.status = 'unpaid'
            else:
                invoice.status = 'partial'
            
            invoice.save()
        
        # Reverse bank transaction
        if payment.deposited_to_account:
            BankTransaction.objects.create(
                account=payment.deposited_to_account,
                transaction_date=timezone.now().date(),
                transaction_type='withdrawal',
                amount=payment.amount,
                balance_after=payment.deposited_to_account.current_balance - payment.amount,
                reference_number=f"BOUNCED-{payment.receipt_number}",
                description=f"Payment bounced - {payment.receipt_number}",
                payment=payment
            )
            
            payment.deposited_to_account.current_balance -= payment.amount
            payment.deposited_to_account.save()
        
        return Response({'status': 'Payment marked as bounced'})

    @action(detail=False, methods=['get'])
    def pending_clearance(self, request):
        """Get payments pending clearance (PDCs)"""
        pending_payments = self.queryset.filter(
            status='pending',
            payment_method='pdc'
        )
        serializer = self.get_serializer(pending_payments, many=True)
        return Response(serializer.data)


# ==================== VENDORS ====================

class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['vendor_type', 'is_active']
    search_fields = ['name', 'vendor_code', 'contact_person', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def outstanding_payments(self, request, pk=None):
        """Get outstanding payments for vendor"""
        vendor = self.get_object()
        outstanding = Expense.objects.filter(
            vendor=vendor,
            status__in=['approved', 'pending']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        return Response({'outstanding_amount': outstanding})

    @action(detail=True, methods=['get'])
    def purchase_history(self, request, pk=None):
        """Get purchase history for vendor"""
        vendor = self.get_object()
        purchases = PurchaseOrder.objects.filter(vendor=vendor).order_by('-po_date')[:10]
        serializer = PurchaseOrderSerializer(purchases, many=True)
        return Response(serializer.data)


# ==================== PURCHASE ORDERS ====================

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all().select_related(
        'vendor', 'project', 'created_by', 'approved_by'
    ).prefetch_related('items')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'vendor', 'project']
    search_fields = ['po_number', 'vendor__name']
    ordering_fields = ['po_date', 'delivery_date', 'total_amount']
    ordering = ['-po_date']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PurchaseOrderDetailSerializer
        return PurchaseOrderSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.employeeprofile)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve purchase order"""
        po = self.get_object()
        
        if po.status != 'pending_approval':
            return Response(
                {'error': 'Only pending POs can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        po.status = 'approved'
        po.approved_by = request.user.employeeprofile
        po.save()
        
        return Response({'status': 'Purchase order approved'})

    @action(detail=True, methods=['post'])
    def mark_received(self, request, pk=None):
        """Mark PO as fully received"""
        po = self.get_object()
        
        # Check if all items are fully received
        all_received = all(
            item.received_quantity >= item.quantity 
            for item in po.items.all()
        )
        
        if all_received:
            po.status = 'received'
            po.save()
            return Response({'status': 'Purchase order marked as received'})
        else:
            return Response(
                {'error': 'Not all items have been received'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PurchaseOrderItemViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer
    permission_classes = [IsAuthenticated]


# ==================== EXPENSES ====================

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all().select_related(
        'project', 'vendor', 'purchase_order', 'paid_from_account',
        'submitted_by', 'approved_by'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category', 'project', 'vendor']
    search_fields = ['expense_number', 'description', 'vendor__name']
    ordering_fields = ['expense_date', 'amount', 'created_at']
    ordering = ['-expense_date']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ExpenseDetailSerializer
        return ExpenseSerializer

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user.employeeprofile)

    @action(detail=True, methods=['post'], permission_classes=[CanApproveExpenses])
    def approve(self, request, pk=None):
        """Approve expense"""
        expense = self.get_object()
        
        if expense.status != 'pending':
            return Response(
                {'error': 'Only pending expenses can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        expense.status = 'approved'
        expense.approved_by = request.user.employeeprofile
        expense.save()
        
        return Response({'status': 'Expense approved'})

    @action(detail=True, methods=['post'], permission_classes=[CanApproveExpenses])
    def reject(self, request, pk=None):
        """Reject expense"""
        expense = self.get_object()
        
        expense.status = 'rejected'
        expense.approved_by = request.user.employeeprofile
        expense.notes = request.data.get('rejection_reason', '')
        expense.save()
        
        return Response({'status': 'Expense rejected'})

    @action(detail=True, methods=['post'], permission_classes=[IsFinanceManager])
    def mark_paid(self, request, pk=None):
        """Mark expense as paid"""
        expense = self.get_object()
        
        if expense.status != 'approved':
            return Response(
                {'error': 'Only approved expenses can be marked as paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        expense.status = 'paid'
        expense.save()
        
        # Create bank transaction if account specified
        if expense.paid_from_account:
            BankTransaction.objects.create(
                account=expense.paid_from_account,
                transaction_date=timezone.now().date(),
                transaction_type='withdrawal',
                amount=expense.total_amount,
                balance_after=expense.paid_from_account.current_balance - expense.total_amount,
                reference_number=expense.expense_number,
                description=f"Expense payment - {expense.description}",
                expense=expense
            )
            
            expense.paid_from_account.current_balance -= expense.total_amount
            expense.paid_from_account.save()
        
        return Response({'status': 'Expense marked as paid'})

    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        """Get expenses pending approval"""
        pending = self.queryset.filter(status='pending')
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expense_summary(self, request):
        """Get expense summary by category"""
        category = request.query_params.get('category')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = self.queryset.filter(status='paid')
        
        if category:
            queryset = queryset.filter(category=category)
        if start_date:
            queryset = queryset.filter(expense_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(expense_date__lte=end_date)
        
        summary = queryset.values('category').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        )
        
        return Response(summary)


# ==================== BANK ACCOUNTS ====================

class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated, IsFinanceManager]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['account_name', 'account_number', 'bank_name']
    ordering_fields = ['bank_name', 'current_balance']
    ordering = ['bank_name']

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get transactions for this account"""
        account = self.get_object()
        transactions = account.transactions.all()[:50]
        serializer = BankTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def balance_history(self, request, pk=None):
        """Get balance history"""
        account = self.get_object()
        days = int(request.query_params.get('days', 30))
        
        start_date = timezone.now().date() - timedelta(days=days)
        transactions = account.transactions.filter(
            transaction_date__gte=start_date
        ).order_by('transaction_date')
        
        serializer = BankTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class BankTransactionViewSet(viewsets.ModelViewSet):
    queryset = BankTransaction.objects.all().select_related('account', 'payment', 'expense')
    serializer_class = BankTransactionSerializer
    permission_classes = [IsAuthenticated, IsFinanceManager]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['account', 'transaction_type']
    ordering_fields = ['transaction_date', 'amount']
    ordering = ['-transaction_date']


# ==================== BUDGETS ====================

class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.all().select_related('project', 'created_by').prefetch_related('line_items')
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['budget_type', 'project']
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BudgetDetailSerializer
        return BudgetSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.employeeprofile)

    @action(detail=True, methods=['get'])
    def variance_analysis(self, request, pk=None):
        """Get budget variance analysis"""
        budget = self.get_object()
        
        line_items = budget.line_items.all()
        variance_data = []
        
        for item in line_items:
            variance = item.allocated_amount - item.spent_amount
            variance_percentage = (variance / item.allocated_amount * 100) if item.allocated_amount > 0 else 0
            
            variance_data.append({
                'category': item.category,
                'allocated': item.allocated_amount,
                'spent': item.spent_amount,
                'variance': variance,
                'variance_percentage': variance_percentage
            })
        
        return Response(variance_data)


class BudgetLineItemViewSet(viewsets.ModelViewSet):
    queryset = BudgetLineItem.objects.all()
    serializer_class = BudgetLineItemSerializer
    permission_classes = [IsAuthenticated]


# ==================== COST TRACKING ====================

class CostCenterViewSet(viewsets.ModelViewSet):
    queryset = CostCenter.objects.all()
    serializer_class = CostCenterSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'name']


class ProjectCostViewSet(viewsets.ModelViewSet):
    queryset = ProjectCost.objects.all().select_related('project', 'cost_center', 'expense')
    serializer_class = ProjectCostSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['project', 'cost_center']
    ordering_fields = ['date', 'actual_amount']
    ordering = ['-date']

    @action(detail=False, methods=['get'])
    def project_summary(self, request):
        """Get cost summary by project"""
        project_id = request.query_params.get('project')
        
        if not project_id:
            return Response(
                {'error': 'Project ID required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        summary = self.queryset.filter(project_id=project_id).values(
            'cost_center__name'
        ).annotate(
            total_budgeted=Sum('budgeted_amount'),
            total_actual=Sum('actual_amount')
        )
        
        return Response(summary)


# ==================== PETTY CASH ====================

class PettyCashAccountViewSet(viewsets.ModelViewSet):
    queryset = PettyCashAccount.objects.all().select_related('custodian')
    serializer_class = PettyCashAccountSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def replenish(self, request, pk=None):
        """Replenish petty cash account"""
        account = self.get_object()
        amount = Decimal(request.data.get('amount', 0))
        
        if amount <= 0:
            return Response(
                {'error': 'Amount must be greater than zero'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create transaction
        PettyCashTransaction.objects.create(
            account=account,
            transaction_date=timezone.now().date(),
            transaction_type='replenishment',
            amount=amount,
            balance_after=account.current_balance + amount,
            description='Petty cash replenishment',
            requested_by=request.user.employeeprofile,
            approved_by=request.user.employeeprofile
        )
        
        account.current_balance += amount
        account.save()
        
        return Response({'status': 'Petty cash replenished', 'new_balance': account.current_balance})


class PettyCashTransactionViewSet(viewsets.ModelViewSet):
    queryset = PettyCashTransaction.objects.all().select_related(
        'account', 'requested_by', 'approved_by'
    )
    serializer_class = PettyCashTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['account', 'transaction_type']
    ordering = ['-transaction_date']


# ==================== ASSETS ====================

class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all().select_related('assigned_to', 'project')
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['asset_type', 'is_active', 'project']
    search_fields = ['asset_code', 'name']
    ordering_fields = ['purchase_date', 'current_value']
    ordering = ['-purchase_date']

    @action(detail=True, methods=['post'])
    def calculate_depreciation(self, request, pk=None):
        """Calculate and update depreciation"""
        asset = self.get_object()
        
        # Simple straight-line depreciation
        years_used = (timezone.now().date() - asset.purchase_date).days / 365.25
        annual_depreciation = (asset.purchase_price - asset.salvage_value) / asset.useful_life_years
        
        asset.accumulated_depreciation = min(
            annual_depreciation * years_used,
            asset.purchase_price - asset.salvage_value
        )
        asset.current_value = asset.purchase_price - asset.accumulated_depreciation
        asset.save()
        
        return Response({
            'accumulated_depreciation': asset.accumulated_depreciation,
            'current_value': asset.current_value
        })

    @action(detail=True, methods=['post'])
    def dispose(self, request, pk=None):
        """Dispose of an asset"""
        asset = self.get_object()
        
        asset.is_active = False
        asset.disposal_date = timezone.now().date()
        asset.disposal_value = Decimal(request.data.get('disposal_value', 0))
        asset.save()
        
        return Response({'status': 'Asset disposed'})


# ==================== COMMISSIONS ====================

class CommissionStructureViewSet(viewsets.ModelViewSet):
    queryset = CommissionStructure.objects.all()
    serializer_class = CommissionStructureSerializer
    permission_classes = [IsAuthenticated, IsFinanceManager]


class CommissionViewSet(viewsets.ModelViewSet):
    queryset = Commission.objects.all().select_related(
        'employee', 'allocation', 'structure'
    )
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'employee', 'allocation']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'], permission_classes=[IsFinanceManager])
    def approve(self, request, pk=None):
        """Approve commission"""
        commission = self.get_object()
        
        if commission.status != 'pending':
            return Response(
                {'error': 'Only pending commissions can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        commission.status = 'approved'
        commission.save()
        
        return Response({'status': 'Commission approved'})

    @action(detail=True, methods=['post'], permission_classes=[IsFinanceManager])
    def mark_paid(self, request, pk=None):
        """Mark commission as paid"""
        commission = self.get_object()
        
        if commission.status != 'approved':
            return Response(
                {'error': 'Only approved commissions can be paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        commission.status = 'paid'
        commission.payment_date = timezone.now().date()
        commission.save()
        
        return Response({'status': 'Commission marked as paid'})


# ==================== FINANCIAL REPORTS ====================

class FinancialPeriodViewSet(viewsets.ModelViewSet):
    queryset = FinancialPeriod.objects.all()
    serializer_class = FinancialPeriodSerializer
    permission_classes = [IsAuthenticated, IsFinanceManager]
    ordering = ['-start_date']

    @action(detail=True, methods=['post'])
    def close_period(self, request, pk=None):
        """Close financial period"""
        period = self.get_object()
        period.is_closed = True
        period.save()
        return Response({'status': 'Period closed'})


class TaxConfigurationViewSet(viewsets.ModelViewSet):
    queryset = TaxConfiguration.objects.all()
    serializer_class = TaxConfigurationSerializer
    permission_classes = [IsAuthenticated, IsFinanceManager]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-effective_from']

    @action(detail=False, methods=['get'])
    def current_rates(self, request):
        """Get currently active tax rates"""
        today = timezone.now().date()
        active_taxes = self.queryset.filter(
            is_active=True,
            effective_from__lte=today
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=today)
        )
        
        serializer = self.get_serializer(active_taxes, many=True)
        return Response(serializer.data)