from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.inventory_dashboard, name='inventory_dashboard'),

    # Fabric Management
    path('fabrics/', views.fabric_list, name='fabric_list'),
    path('fabrics/add/', views.add_fabric, name='add_fabric'),
    path('fabrics/<int:pk>/edit/', views.edit_fabric, name='edit_fabric'),
    path('fabrics/<int:pk>/add-stock/', views.add_fabric_stock, name='add_fabric_stock'),
    path('fabrics/<int:pk>/adjust/', views.fabric_stock_adjust, name='fabric_stock_adjust'),
    path('fabrics/<int:pk>/ledger/', views.fabric_stock_ledger, name='fabric_stock_ledger'),

    # Trim Management
    path('trims/', views.trim_list, name='trim_list'),
    path('trims/add/', views.add_trim, name='add_trim'),
    path('trims/<int:pk>/edit/', views.edit_trim, name='edit_trim'),
    path('trims/<int:pk>/add-stock/', views.add_trim_stock, name='add_trim_stock'),
    path('trims/<int:pk>/ledger/', views.trim_stock_ledger, name='trim_stock_ledger'),

    # Goods Receipt (fabric) - legacy, kept for historical records/direct links only
    path('receipts/', views.goods_receipts, name='goods_receipts'),
    path('receipts/add/', views.add_goods_receipt, name='add_goods_receipt'),

    # Trim Receipt - legacy, kept for historical records/direct links only
    path('trim-receipts/', views.trim_receipts, name='trim_receipts'),
    path('trim-receipts/add/', views.add_trim_receipt, name='add_trim_receipt'),

    # Production Issues - legacy, kept for historical records/direct links only
    path('issues/', views.production_issues, name='production_issues'),
    path('issues/add/', views.add_production_issue, name='add_production_issue'),

    # Finished Goods
    path('finished-goods/', views.finished_goods_list, name='finished_goods_list'),
    path('finished-goods/add/', views.add_finished_goods, name='add_finished_goods'),
    path('finished-goods/<int:pk>/edit/', views.edit_finished_goods, name='edit_finished_goods'),
    path('finished-goods/<int:pk>/add-stock/', views.add_finished_goods_stock, name='add_finished_goods_stock'),
    path('finished-goods/<int:pk>/ledger/', views.finished_goods_stock_ledger, name='finished_goods_stock_ledger'),

    # Dispatches
    path('dispatches/', views.dispatches, name='dispatches'),
    path('dispatches/add/', views.add_dispatch, name='add_dispatch'),
    path('dispatches/<int:pk>/', views.dispatch_detail, name='dispatch_detail'),
    path('dispatches/<int:pk>/edit/', views.edit_dispatch, name='edit_dispatch'),
    path('dispatches/<int:pk>/status/', views.update_dispatch_status, name='update_dispatch_status'),
    path('dispatches/<int:pk>/approve-shipment/', views.approve_dispatch_shipment, name='approve_dispatch_shipment'),
    path('dispatches/<int:pk>/reject-shipment/', views.reject_dispatch_shipment, name='reject_dispatch_shipment'),

    # Stock Adjustments
    path('adjustments/', views.stock_adjustments, name='stock_adjustments'),
    path('adjustments/add/', views.add_stock_adjustment, name='add_stock_adjustment'),
    path('adjustments/pending/', views.pending_adjustments, name='pending_adjustments'),
    path('adjustments/<int:pk>/', views.stock_adjustment_detail, name='stock_adjustment_detail'),
    path('adjustments/<int:pk>/approve/', views.approve_stock_adjustment, name='approve_stock_adjustment'),
    path('adjustments/<int:pk>/reject/', views.reject_stock_adjustment, name='reject_stock_adjustment'),

    # Reports
    path('reports/', views.stock_report, name='stock_report'),
    path('reports/export/excel/', views.stock_report_export_excel, name='stock_report_export_excel'),
    path('reports/export/pdf/', views.stock_report_export_pdf, name='stock_report_export_pdf'),
]
