from django.contrib import admin

from .models import (
    ChartOfAccount, Buyer, Supplier, Style, PurchaseOrder, PurchaseOrderItem,
    SalesInvoice, SalesInvoiceItem, Payment, JournalEntry, JournalDetail,
    CostSheet, BankAccount, BankTransaction,
)

admin.site.register(ChartOfAccount)
admin.site.register(Buyer)
admin.site.register(Supplier)
admin.site.register(Style)
admin.site.register(PurchaseOrder)
admin.site.register(PurchaseOrderItem)
admin.site.register(SalesInvoice)
admin.site.register(SalesInvoiceItem)
admin.site.register(Payment)
admin.site.register(JournalEntry)
admin.site.register(JournalDetail)
admin.site.register(CostSheet)
admin.site.register(BankAccount)
admin.site.register(BankTransaction)
