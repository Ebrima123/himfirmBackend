# finance/api_endpoints.py
"""
Finance Module API Endpoints Documentation
==========================================

All endpoints require authentication unless specified otherwise.
Base URL: /api/finance/

INVOICING & BILLING
-------------------

Invoices:
GET     /invoices/                          - List all invoices
POST    /invoices/                          - Create new invoice
GET     /invoices/{id}/                     - Retrieve invoice details
PUT     /invoices/{id}/                     - Update invoice
PATCH   /invoices/{id}/                     - Partial update invoice
DELETE  /invoices/{id}/                     - Delete invoice
POST    /invoices/{id}/approve/             - Approve invoice
POST    /invoices/{id}/send_to_customer/    - Send invoice to customer
POST    /invoices/{id}/mark_paid/           - Mark invoice as paid
GET     /invoices/overdue/                  - List overdue invoices
GET     /invoices/dashboard/                - Get invoice statistics

Invoice Line Items:
GET     /invoice-line-items/                - List all line items
POST    /invoice-line-items/                - Create line item
GET     /invoice-line-items/{id}/           - Retrieve line item
PUT     /invoice-line-items/{id}/           - Update line item
DELETE  /invoice-line-items/{id}/           - Delete line item

Payments:
GET     /payments/                          - List all payments
POST    /payments/                          - Create payment
GET     /payments/{id}/                     - Retrieve payment details
PUT     /payments/{id}/                     - Update payment
DELETE  /payments/{id}/                     - Delete payment
POST    /payments/{id}/mark_bounced/        - Mark payment as bounced
GET     /payments/pending_clearance/        - List pending PDCs

VENDOR MANAGEMENT
-----------------

Vendors:
GET     /vendors/                           - List all vendors
POST    /vendors/                           - Create vendor
GET     /vendors/{id}/                      - Retrieve vendor details
PUT     /vendors/{id}/                      - Update vendor
DELETE  /vendors/{id}/                      - Delete vendor
GET     /vendors/{id}/outstanding_payments/ - Get vendor outstanding
GET     /vendors/{id}/purchase_history/     - Get vendor purchase history

Purchase Orders:
GET     /purchase-orders/                   - List all POs
POST    /purchase-orders/                   - Create PO
GET     /purchase-orders/{id}/              - Retrieve PO details
PUT     /purchase-orders/{id}/              - Update PO
DELETE  /purchase-orders/{id}/              - Delete PO
POST    /purchase-orders/{id}/approve/      - Approve PO
POST    /purchase-orders/{id}/mark_received/ - Mark PO as received

PO Items:
GET     /purchase-order-items/              - List all PO items
POST    /purchase-order-items/              - Create PO item
GET     /purchase-order-items/{id}/         - Retrieve PO item
PUT     /purchase-order-items/{id}/         - Update PO item
DELETE  /purchase-order-items/{id}/         - Delete PO item

EXPENSES
--------

GET     /expenses/                          - List all expenses
POST    /expenses/                          - Create expense
GET     /expenses/{id}/                     - Retrieve expense details
PUT     /expenses/{id}/                     - Update expense
DELETE  /expenses/{id}/                     - Delete expense
POST    /expenses/{id}/approve/             - Approve expense (requires permission)
POST    /expenses/{id}/reject/              - Reject expense (requires permission)
POST    /expenses/{id}/mark_paid/           - Mark expense as paid (finance manager)
GET     /expenses/pending_approval/         - List pending expenses
GET     /expenses/expense_summary/          - Get expense summary by category
        Query params: category, start_date, end_date

BANKING
-------

Bank Accounts:
GET     /bank-accounts/                     - List all bank accounts
POST    /bank-accounts/                     - Create bank account
GET     /bank-accounts/{id}/                - Retrieve account details
PUT     /bank-accounts/{id}/                - Update account
DELETE  /bank-accounts/{id}/                - Delete account
GET     /bank-accounts/{id}/transactions/   - Get account transactions
GET     /bank-accounts/{id}/balance_history/ - Get balance history
        Query params: days (default: 30)

Bank Transactions:
GET     /bank-transactions/                 - List all transactions
POST    /bank-transactions/                 - Create transaction
GET     /bank-transactions/{id}/            - Retrieve transaction
PUT     /bank-transactions/{id}/            - Update transaction
DELETE  /bank-transactions/{id}/            - Delete transaction

BUDGETING
---------

Budgets:
GET     /budgets/                           - List all budgets
POST    /budgets/                           - Create budget
GET     /budgets/{id}/                      - Retrieve budget details
PUT     /budgets/{id}/                      - Update budget
DELETE  /budgets/{id}/                      - Delete budget
GET     /budgets/{id}/variance_analysis/    - Get variance analysis

Budget Line Items:
GET     /budget-line-items/                 - List all line items
POST    /budget-line-items/                 - Create line item
GET     /budget-line-items/{id}/            - Retrieve line item
PUT     /budget-line-items/{id}/            - Update line item
DELETE  /budget-line-items/{id}/            - Delete line item

COST TRACKING
-------------

Cost Centers:
GET     /cost-centers/                      - List all cost centers
POST    /cost-centers/                      - Create cost center
GET     /cost-centers/{id}/                 - Retrieve cost center
PUT     /cost-centers/{id}/                 - Update cost center
DELETE  /cost-centers/{id}/                 - Delete cost center

Project Costs:
GET     /project-costs/                     - List all project costs
POST    /project-costs/                     - Create project cost
GET     /project-costs/{id}/                - Retrieve cost
PUT     /project-costs/{id}/                - Update cost
DELETE  /project-costs/{id}/                - Delete cost
GET     /project-costs/project_summary/     - Get project cost summary
        Query params: project (required)

FINANCIAL PERIODS & TAX
-----------------------

Financial Periods:
GET     /financial-periods/                 - List all periods
POST    /financial-periods/                 - Create period
GET     /financial-periods/{id}/            - Retrieve period
PUT     /financial-periods/{id}/            - Update period
DELETE  /financial-periods/{id}/            - Delete period
POST    /financial-periods/{id}/close_period/ - Close period

Tax Configurations:
GET     /tax-configurations/                - List all tax configs
POST    /tax-configurations/                - Create tax config
GET     /tax-configurations/{id}/           - Retrieve tax config
PUT     /tax-configurations/{id}/           - Update tax config
DELETE  /tax-configurations/{id}/           - Delete tax config
GET     /tax-configurations/current_rates/  - Get current active rates

PETTY CASH
----------

Petty Cash Accounts:
GET     /petty-cash-accounts/               - List all accounts
POST    /petty-cash-accounts/               - Create account
GET     /petty-cash-accounts/{id}/          - Retrieve account
PUT     /petty-cash-accounts/{id}/          - Update account
DELETE  /petty-cash-accounts/{id}/          - Delete account
POST    /petty-cash-accounts/{id}/replenish/ - Replenish account
        Body: { "amount": 1000.00 }

Petty Cash Transactions:
GET     /petty-cash-transactions/           - List all transactions
POST    /petty-cash-transactions/           - Create transaction
GET     /petty-cash-transactions/{id}/      - Retrieve transaction
PUT     /petty-cash-transactions/{id}/      - Update transaction
DELETE  /petty-cash-transactions/{id}/      - Delete transaction

ASSETS
------

GET     /assets/                            - List all assets
POST    /assets/                            - Create asset
GET     /assets/{id}/                       - Retrieve asset details
PUT     /assets/{id}/                       - Update asset
DELETE  /assets/{id}/                       - Delete asset
POST    /assets/{id}/calculate_depreciation/ - Calculate depreciation
POST    /assets/{id}/dispose/               - Dispose asset
        Body: { "disposal_value": 5000.00 }

COMMISSIONS
-----------

Commission Structures:
GET     /commission-structures/             - List all structures
POST    /commission-structures/             - Create structure
GET     /commission-structures/{id}/        - Retrieve structure
PUT     /commission-structures/{id}/        - Update structure
DELETE  /commission-structures/{id}/        - Delete structure

Commissions:
GET     /commissions/                       - List all commissions
POST    /commissions/                       - Create commission
GET     /commissions/{id}/                  - Retrieve commission
PUT     /commissions/{id}/                  - Update commission
DELETE  /commissions/{id}/                  - Delete commission
POST    /commissions/{id}/approve/          - Approve commission (finance manager)
POST    /commissions/{id}/mark_paid/        - Mark commission as paid (finance manager)

FILTERING & SEARCH
------------------

Most list endpoints support filtering, searching, and ordering:

Filter by fields:
    ?status=pending
    ?project=123
    ?category=material
    ?vendor=456

Search:
    ?search=invoice_number

Ordering:
    ?ordering=-created_at
    ?ordering=amount

Pagination:
    ?page=1
    ?page_size=50

Date ranges:
    ?start_date=2024-01-01
    ?end_date=2024-12-31

COMMON RESPONSE FORMATS
-----------------------

Success (List):
{
    "count": 100,
    "next": "http://api/finance/invoices/?page=2",
    "previous": null,
    "results": [...]
}

Success (Detail):
{
    "id": 1,
    "field1": "value1",
    ...
}

Error:
{
    "error": "Error message",
    "detail": "Detailed error description"
}

Validation Error:
{
    "field_name": ["Error message"]
}

PERMISSIONS
-----------

IsAuthenticated: All endpoints
IsFinanceManager: Bank accounts, approvals, tax configs
IsAccountant: Financial data access
CanApproveExpenses: Expense approvals
CanManageVendors: Vendor modifications

COMMON QUERY PARAMETERS
-----------------------

Invoices:
- status: draft, pending_approval, approved, sent, unpaid, partial, paid, overdue, cancelled
- invoice_type: sale, advance, progress, final, retention, credit_note, debit_note
- customer: customer_id
- project: project_id

Expenses:
- status: pending, approved, paid, rejected
- category: material, labor, equipment, subcontractor, utilities, office, travel, marketing, legal, insurance, permits, maintenance, other
- project: project_id
- vendor: vendor_id

Payments:
- status: pending, cleared, bounced, cancelled
- payment_method: cash, cheque, bank_transfer, credit_card, debit_card, online, pdc, dd
- customer: customer_id

Assets:
- asset_type: land, building, vehicle, equipment, machinery, furniture, it_equipment, other
- is_active: true/false
- project: project_id
"""