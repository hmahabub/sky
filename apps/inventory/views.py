from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Count, Q, F
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta, date
import json
import csv
from decimal import Decimal, InvalidOperation

from .models import (
    Fabric, FabricRoll, Trim, GoodsReceipt, GoodsReceiptDetail,
    TrimReceipt, TrimReceiptDetail,
    ProductionIssue, ProductionIssueDetail, FinishedGoods,
    FinishedGoodsProduction, Dispatch, DispatchDetail,
    StockMovement, StockAdjustment, StockAdjustmentDetail,
    Machine, MachineEvent, SparePart, SparePartConsumption,
    StationeryItem, StationeryConsumption, SupplyAdjustment,
)
from .forms import (
    FabricForm, FabricRollForm, FabricStockInForm, FabricLotAdjustForm,
    TrimForm, TrimStockInForm, GoodsReceiptForm,
    GoodsReceiptDetailForm, TrimReceiptForm, TrimReceiptDetailForm,
    ProductionIssueForm, ProductionIssueDetailForm,
    FinishedGoodsForm, FinishedGoodsStockInForm,
    DispatchForm, DispatchDetailForm, StockAdjustmentForm, RejectStockAdjustmentForm,
    MachineForm, MachineEventForm, RejectMachineEventForm,
    SparePartForm, SparePartStockInForm, SparePartConsumptionForm,
    StationeryItemForm, StationeryStockInForm, StationeryConsumptionForm,
    SupplyAdjustmentForm, RejectSupplyAdjustmentForm,
)

def is_inventory_or_admin(user):
    return user.is_superuser or user.groups.filter(name='Inventory').exists()

@login_required
def inventory_dashboard(request):
    """Inventory Dashboard Overview"""
    context = {
        'active': 'inventory',
        'page_title': 'Inventory Dashboard',
    }
    
    # Summary Statistics
    context['total_fabrics'] = Fabric.objects.filter(is_active=True).count()
    context['total_trims'] = Trim.objects.filter(is_active=True).count()
    context['total_finished_goods'] = FinishedGoods.objects.filter(is_active=True).count()
    
    # Stock Status
    fabric_stock = Fabric.objects.aggregate(total=Sum('current_stock'))['total'] or 0
    trim_stock = Trim.objects.aggregate(total=Sum('current_stock'))['total'] or 0
    finished_stock = FinishedGoods.objects.aggregate(total=Sum('quantity_in_stock'))['total'] or 0
    
    context['total_fabric_stock'] = fabric_stock
    context['total_trim_stock'] = trim_stock
    context['total_finished_stock'] = finished_stock
    
    # Low Stock Items
    context['low_fabric_count'] = Fabric.objects.filter(
        current_stock__lte=F('min_stock'),
        is_active=True
    ).count()
    
    context['low_trim_count'] = Trim.objects.filter(
        current_stock__lte=500,  # Adjust based on reorder level
        is_active=True
    ).count()
    
    # Assets & Supplies
    context['total_machines'] = Machine.objects.exclude(status__in=['sold', 'scrapped']).count()
    context['machines_needing_attention'] = Machine.objects.filter(
        status__in=['under_maintenance', 'broken_down']
    ).count()

    context['total_spare_parts'] = SparePart.objects.filter(is_active=True).count()
    context['spare_parts_stock'] = SparePart.objects.filter(is_active=True).aggregate(
        total=Sum('current_stock')
    )['total'] or 0
    context['low_spare_parts_count'] = SparePart.objects.filter(
        current_stock__lte=F('min_stock'), is_active=True
    ).count()

    context['total_stationery_items'] = StationeryItem.objects.filter(is_active=True).count()
    context['stationery_stock'] = StationeryItem.objects.filter(is_active=True).aggregate(
        total=Sum('current_stock')
    )['total'] or 0
    context['low_stationery_count'] = StationeryItem.objects.filter(
        current_stock__lte=F('min_stock'), is_active=True
    ).count()

    # Recent Receipts
    context['recent_receipts'] = GoodsReceipt.objects.select_related('supplier').order_by('-receipt_date')[:5]
    
    # Recent Dispatches
    context['recent_dispatches'] = Dispatch.objects.select_related('project').order_by('-dispatch_date')[:5]
    
    # Stock Movement Chart Data
    last_7_days = [date.today() - timedelta(days=x) for x in range(6, -1, -1)]
    movement_data = []
    
    for day in last_7_days:
        count = StockMovement.objects.filter(movement_date=day).count()
        movement_data.append(count)
    
    context['movement_labels'] = [day.strftime('%b %d') for day in last_7_days]
    context['movement_data'] = movement_data
    
    # Top Items by Stock Value
    top_fabrics = Fabric.objects.filter(is_active=True).order_by('-current_stock')[:5]
    top_trims = Trim.objects.filter(is_active=True).order_by('-current_stock')[:5]
    
    context['top_fabrics'] = top_fabrics
    context['top_trims'] = top_trims
    
    return render(request, 'inventory/dashboard.html', context)

@login_required
def fabric_list(request):
    """List all fabrics"""
    fabrics = Fabric.objects.filter(is_active=True).select_related('supplier')
    
    # Search
    search = request.GET.get('search')
    if search:
        fabrics = fabrics.filter(
            Q(fabric_name__icontains=search) |
            Q(color__icontains=search)
        )

    # Filter by fabric type
    fabric_type = request.GET.get('type')
    if fabric_type:
        fabrics = fabrics.filter(fabric_type=fabric_type)

    # Filter by stock status
    stock_status = request.GET.get('stock_status')
    if stock_status == 'low':
        fabrics = fabrics.filter(current_stock__lte=F('min_stock'))
    elif stock_status == 'normal':
        fabrics = fabrics.filter(current_stock__gt=F('min_stock'), current_stock__lt=F('max_stock'))
    elif stock_status == 'overstock':
        fabrics = fabrics.filter(current_stock__gte=F('max_stock'))
    
    # Pagination
    paginator = Paginator(fabrics, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'active': 'inventory',
        'page_title': 'Fabric Management',
        'fabrics': page_obj,
        'fabric_types': Fabric.FABRIC_TYPES,
        'search': search,
        'current_type': fabric_type,
        'current_stock_status': stock_status,
    }
    return render(request, 'inventory/fabric_list.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_fabric(request):
    """Add new fabric, optionally with its first stock lot."""
    if request.method == 'POST':
        form = FabricForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                fabric = form.save()

                lot_number = form.cleaned_data.get('lot_number')
                initial_quantity = form.cleaned_data.get('initial_quantity') or Decimal('0')
                if lot_number:
                    roll = FabricRoll.objects.create(
                        roll_number=lot_number,
                        lot_number=lot_number,
                        fabric=fabric,
                        length=initial_quantity,
                        location='Main Warehouse',
                        received_date=date.today(),
                        quality_status='passed',
                    )
                    if initial_quantity > 0:
                        fabric.current_stock = initial_quantity
                        fabric.save(update_fields=['current_stock'])
                        StockMovement.objects.create(
                            movement_type='receipt',
                            reference_number=f"LOT-{lot_number}",
                            reference_id=roll.pk,
                            fabric=fabric,
                            fabric_roll=roll,
                            quantity=initial_quantity,
                            notes=f"Starting lot {lot_number}",
                            created_by=request.user,
                        )

            messages.success(request, f'Fabric "{fabric.fabric_name}" added successfully!')
            return redirect('inventory:fabric_list')
    else:
        form = FabricForm()

    context = {
        'active': 'inventory',
        'page_title': 'Add Fabric',
        'form': form,
    }
    return render(request, 'inventory/fabric_form.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def edit_fabric(request, pk):
    """Edit fabric"""
    fabric = get_object_or_404(Fabric, pk=pk)
    if request.method == 'POST':
        form = FabricForm(request.POST, instance=fabric)
        if form.is_valid():
            form.save()
            messages.success(request, f'Fabric "{fabric.fabric_name}" updated successfully!')
            return redirect('inventory:fabric_list')
    else:
        form = FabricForm(instance=fabric)
    
    context = {
        'active': 'inventory',
        'page_title': 'Edit Fabric',
        'form': form,
        'fabric': fabric,
    }
    return render(request, 'inventory/fabric_form.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_fabric_stock(request, pk):
    """
    Add a brand-new lot to an existing fabric. Immediate, no approval
    needed (same as the old Goods Receipt this replaces) - approval only
    gates stock going OUT (fabric_stock_adjust), not coming in.
    """
    fabric = get_object_or_404(Fabric, pk=pk)
    if request.method == 'POST':
        form = FabricStockInForm(request.POST)
        if form.is_valid():
            lot_number = form.cleaned_data['lot_number']
            quantity = form.cleaned_data['quantity']
            with transaction.atomic():
                roll = FabricRoll.objects.create(
                    roll_number=lot_number,
                    lot_number=lot_number,
                    fabric=fabric,
                    length=quantity,
                    location=form.cleaned_data['location'],
                    received_date=form.cleaned_data['received_date'],
                    quality_status='passed',
                )
                Fabric.objects.filter(pk=fabric.pk).update(current_stock=F('current_stock') + quantity)
                StockMovement.objects.create(
                    movement_type='receipt',
                    reference_number=f"LOT-{lot_number}",
                    reference_id=roll.pk,
                    fabric=fabric,
                    fabric_roll=roll,
                    quantity=quantity,
                    notes=form.cleaned_data['notes'],
                    created_by=request.user,
                )
            messages.success(request, f'Lot "{lot_number}" added - {quantity} {fabric.get_unit_display()} in stock.')
            return redirect('inventory:fabric_stock_ledger', pk=fabric.pk)
    else:
        form = FabricStockInForm()

    context = {
        'active': 'inventory',
        'page_title': 'Add Stock',
        'form': form,
        'fabric': fabric,
    }
    return render(request, 'inventory/fabric_stock_in_form.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def fabric_stock_adjust(request, pk):
    """
    Lot-wise Adjust/Issue for a fabric: pick one or more in-stock lots and
    enter a quantity against each. Creates a 'pending' StockAdjustment (+
    one StockAdjustmentDetail per lot) - no stock actually moves until a
    superuser approves it (see approve_stock_adjustment).
    """
    fabric = get_object_or_404(Fabric, pk=pk)
    lots = FabricRoll.objects.filter(fabric=fabric, status='in_stock').order_by('received_date')

    if request.method == 'POST':
        form = FabricLotAdjustForm(request.POST)
        rows = []
        row_errors = []
        for lot in lots:
            raw = request.POST.get(f'quantity_{lot.pk}')
            if not raw:
                continue
            try:
                qty = Decimal(raw)
            except InvalidOperation:
                row_errors.append(f"Lot {lot.lot_number}: quantity must be a number.")
                continue
            if qty <= 0:
                continue
            rows.append((lot, qty))

        if form.is_valid():
            if not rows and not row_errors:
                row_errors.append("Enter a quantity against at least one lot.")

            if row_errors:
                for err in row_errors:
                    messages.error(request, err)
            else:
                adjustment = StockAdjustment.objects.create(
                    adjustment_type=form.cleaned_data['adjustment_type'],
                    direction=form.cleaned_data['direction'],
                    fabric=fabric,
                    purchase_order=form.cleaned_data['purchase_order'],
                    adjustment_date=form.cleaned_data['adjustment_date'],
                    quantity=sum((qty for _, qty in rows), Decimal('0')),
                    reason=form.cleaned_data['reason'],
                    notes=form.cleaned_data['notes'],
                    status='pending',
                    created_by=request.user,
                )
                StockAdjustmentDetail.objects.bulk_create([
                    StockAdjustmentDetail(stock_adjustment=adjustment, fabric_roll=lot, quantity=qty)
                    for lot, qty in rows
                ])
                messages.success(
                    request,
                    f'Adjustment "{adjustment.adjustment_number}" submitted for approval across {len(rows)} lot(s).'
                )
                return redirect('inventory:fabric_stock_ledger', pk=fabric.pk)
    else:
        form = FabricLotAdjustForm()

    context = {
        'active': 'inventory',
        'page_title': 'Adjust / Issue Stock',
        'form': form,
        'fabric': fabric,
        'lots': lots,
    }
    return render(request, 'inventory/fabric_lot_adjust_form.html', context)

@login_required
def trim_list(request):
    """List all trims"""
    trims = Trim.objects.filter(is_active=True).select_related('supplier')
    
    # Search
    search = request.GET.get('search')
    if search:
        trims = trims.filter(
            Q(trim_name__icontains=search) |
            Q(color__icontains=search) |
            Q(size__icontains=search)
        )
    
    # Filter by trim type
    trim_type = request.GET.get('type')
    if trim_type:
        trims = trims.filter(trim_type=trim_type)
    
    context = {
        'active': 'inventory',
        'page_title': 'Trim Management',
        'trims': trims,
        'trim_types': Trim.TRIM_TYPES,
        'search': search,
        'current_type': trim_type,
    }
    return render(request, 'inventory/trim_list.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_trim(request):
    """Add new trim"""
    if request.method == 'POST':
        form = TrimForm(request.POST)
        if form.is_valid():
            trim = form.save()
            messages.success(request, f'Trim "{trim.trim_name}" added successfully!')
            return redirect('inventory:trim_list')
    else:
        form = TrimForm()
    
    context = {
        'active': 'inventory',
        'page_title': 'Add Trim',
        'form': form,
    }
    return render(request, 'inventory/trim_form.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def edit_trim(request, pk):
    """Edit trim"""
    trim = get_object_or_404(Trim, pk=pk)
    if request.method == 'POST':
        form = TrimForm(request.POST, instance=trim)
        if form.is_valid():
            form.save()
            messages.success(request, f'Trim "{trim.trim_name}" updated successfully!')
            return redirect('inventory:trim_list')
    else:
        form = TrimForm(instance=trim)

    context = {
        'active': 'inventory',
        'page_title': 'Edit Trim',
        'form': form,
        'trim': trim,
    }
    return render(request, 'inventory/trim_form.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_trim_stock(request, pk):
    """
    Add stock to an existing trim item. Deliberately simple (no lot
    tracking - trims aren't batch/dye-lot sensitive the way fabric is).
    Immediate, no approval needed (same as Add Stock for Fabric/Finished
    Goods) - approval only gates stock going OUT via Stock Adjustment.
    """
    trim = get_object_or_404(Trim, pk=pk)
    if request.method == 'POST':
        form = TrimStockInForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            with transaction.atomic():
                Trim.objects.filter(pk=trim.pk).update(current_stock=F('current_stock') + quantity)
                movement = StockMovement.objects.create(
                    movement_type='receipt',
                    reference_number='',
                    reference_id=trim.pk,
                    trim=trim,
                    quantity=quantity,
                    notes=form.cleaned_data['notes'],
                    created_by=request.user,
                )
                movement.reference_number = movement.movement_number
                movement.save(update_fields=['reference_number'])
            messages.success(request, f'Added {quantity} units to "{trim.trim_name}" stock.')
            return redirect('inventory:trim_stock_ledger', pk=trim.pk)
    else:
        form = TrimStockInForm()

    context = {
        'active': 'inventory',
        'page_title': 'Add Stock',
        'form': form,
        'trim': trim,
    }
    return render(request, 'inventory/trim_stock_in_form.html', context)

@login_required
def goods_receipts(request):
    """List all goods receipts"""
    receipts = GoodsReceipt.objects.select_related('supplier').all()
    
    context = {
        'active': 'inventory',
        'page_title': 'Goods Receipts',
        'receipts': receipts,
    }
    return render(request, 'inventory/goods_receipts.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_goods_receipt(request):
    """
    Create a Goods Receipt: adds one or more fabrics to stock.
    A GR only ever increases stock - reductions go through Stock Adjustment.
    """
    if request.method == 'POST':
        form = GoodsReceiptForm(request.POST)
        if form.is_valid():
            fabric_ids = request.POST.getlist('fabric_ids[]')
            quantities = request.POST.getlist('quantities[]')
            unit_prices = request.POST.getlist('unit_prices[]')

            row_errors = []
            rows = []

            for i in range(len(quantities)):
                if not quantities[i]:
                    continue

                fabric_id = fabric_ids[i] if i < len(fabric_ids) and fabric_ids[i] else None
                if not fabric_id:
                    row_errors.append(f"Row {i + 1}: select a fabric.")
                    continue

                try:
                    quantity = Decimal(quantities[i])
                    unit_price = Decimal(unit_prices[i] or 0)
                except InvalidOperation:
                    row_errors.append(f"Row {i + 1}: quantity and price must be valid numbers.")
                    continue

                if quantity <= 0:
                    row_errors.append(f"Row {i + 1}: quantity must be greater than 0.")
                    continue

                rows.append({
                    'fabric_id': fabric_id,
                    'quantity': quantity,
                    'unit_price': unit_price,
                })

            if not rows and not row_errors:
                row_errors.append("Add at least one fabric to the receipt.")

            if row_errors:
                for err in row_errors:
                    messages.error(request, err)
            else:
                with transaction.atomic():
                    receipt = form.save(commit=False)
                    receipt.received_by = request.user
                    receipt.save()

                    total_quantity = Decimal('0')

                    for row in rows:
                        detail = GoodsReceiptDetail.objects.create(
                            goods_receipt=receipt,
                            fabric_id=row['fabric_id'],
                            quantity=row['quantity'],
                            unit_price=row['unit_price'],
                        )

                        total_quantity += detail.quantity

                        # Update stock with an F() expression so concurrent
                        # receipts can't clobber each other's stock updates.
                        Fabric.objects.filter(pk=detail.fabric_id).update(
                            current_stock=F('current_stock') + detail.quantity
                        )

                        StockMovement.objects.create(
                            movement_type='receipt',
                            reference_number=receipt.receipt_number,
                            reference_id=receipt.pk,
                            fabric_id=detail.fabric_id,
                            quantity=detail.quantity,
                            notes=f"Goods receipt from {receipt.supplier.supplier_name}",
                            created_by=request.user,
                        )

                    receipt.total_quantity = total_quantity
                    receipt.save()

                messages.success(request, f'Goods receipt "{receipt.receipt_number}" created - stock updated!')
                return redirect('inventory:goods_receipts')
    else:
        form = GoodsReceiptForm()
    
    context = {
        'active': 'inventory',
        'page_title': 'Add Goods Receipt',
        'form': form,
        'fabrics': Fabric.objects.filter(is_active=True),
    }
    return render(request, 'inventory/goods_receipt_form.html', context)

@login_required
def fabric_stock_ledger(request, pk):
    """
    All stock-affecting activity (lot additions, issues/adjustments) for a
    single fabric, newest first, with a running balance - plus its current
    lot breakdown.
    """
    fabric = get_object_or_404(Fabric, pk=pk)
    movements = list(
        StockMovement.objects.filter(fabric=fabric).order_by('movement_date', 'created_at')
    )

    # Work out a running balance ending at the fabric's current stock, so
    # the ledger reads naturally even though we're computing it after the
    # fact from a signed-quantity log.
    total_delta = sum((m.quantity for m in movements), Decimal('0'))
    running_balance = fabric.current_stock - total_delta
    for movement in movements:
        running_balance += movement.quantity
        movement.balance_after = running_balance

    movements.reverse()  # newest first for display

    lots = FabricRoll.objects.filter(fabric=fabric).order_by('-received_date')

    context = {
        'active': 'inventory',
        'page_title': f'Stock Ledger - {fabric.fabric_name}',
        'fabric': fabric,
        'movements': movements,
        'lots': lots,
    }
    return render(request, 'inventory/fabric_stock_ledger.html', context)

@login_required
def trim_receipts(request):
    """List all trim receipts"""
    receipts = TrimReceipt.objects.select_related('supplier').all()

    context = {
        'active': 'inventory',
        'page_title': 'Trim Receipts',
        'receipts': receipts,
    }
    return render(request, 'inventory/trim_receipts.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_trim_receipt(request):
    """
    Create a Trim Receipt: adds one or more trims to stock.
    Mirrors add_goods_receipt exactly, just for trims. A TR only ever
    increases stock - reductions go through Stock Adjustment.
    """
    if request.method == 'POST':
        form = TrimReceiptForm(request.POST)
        if form.is_valid():
            trim_ids = request.POST.getlist('trim_ids[]')
            quantities = request.POST.getlist('quantities[]')
            unit_prices = request.POST.getlist('unit_prices[]')

            row_errors = []
            rows = []

            for i in range(len(quantities)):
                if not quantities[i]:
                    continue

                trim_id = trim_ids[i] if i < len(trim_ids) and trim_ids[i] else None
                if not trim_id:
                    row_errors.append(f"Row {i + 1}: select a trim.")
                    continue

                try:
                    quantity = int(quantities[i])
                    unit_price = Decimal(unit_prices[i] or 0)
                except (ValueError, InvalidOperation):
                    row_errors.append(f"Row {i + 1}: quantity must be a whole number and price must be valid.")
                    continue

                if quantity <= 0:
                    row_errors.append(f"Row {i + 1}: quantity must be greater than 0.")
                    continue

                rows.append({
                    'trim_id': trim_id,
                    'quantity': quantity,
                    'unit_price': unit_price,
                })

            if not rows and not row_errors:
                row_errors.append("Add at least one trim to the receipt.")

            if row_errors:
                for err in row_errors:
                    messages.error(request, err)
            else:
                with transaction.atomic():
                    receipt = form.save(commit=False)
                    receipt.received_by = request.user
                    receipt.save()

                    total_quantity = 0

                    for row in rows:
                        detail = TrimReceiptDetail.objects.create(
                            trim_receipt=receipt,
                            trim_id=row['trim_id'],
                            quantity=row['quantity'],
                            unit_price=row['unit_price'],
                        )

                        total_quantity += detail.quantity

                        # Update stock with an F() expression so concurrent
                        # receipts can't clobber each other's stock updates.
                        Trim.objects.filter(pk=detail.trim_id).update(
                            current_stock=F('current_stock') + detail.quantity
                        )

                        StockMovement.objects.create(
                            movement_type='receipt',
                            reference_number=receipt.receipt_number,
                            reference_id=receipt.pk,
                            trim_id=detail.trim_id,
                            quantity=detail.quantity,
                            notes=f"Trim receipt from {receipt.supplier.supplier_name}",
                            created_by=request.user,
                        )

                    receipt.total_quantity = total_quantity
                    receipt.save()

                messages.success(request, f'Trim receipt "{receipt.receipt_number}" created - stock updated!')
                return redirect('inventory:trim_receipts')
    else:
        form = TrimReceiptForm()

    context = {
        'active': 'inventory',
        'page_title': 'Add Trim Receipt',
        'form': form,
        'trims': Trim.objects.filter(is_active=True),
    }
    return render(request, 'inventory/trim_receipt_form.html', context)

@login_required
def trim_stock_ledger(request, pk):
    """
    All stock-affecting activity (Trim Receipts and Stock Adjustments) for
    a single trim, newest first, with a running balance.
    """
    trim = get_object_or_404(Trim, pk=pk)
    movements = list(
        StockMovement.objects.filter(trim=trim).order_by('movement_date', 'created_at')
    )

    total_delta = sum((m.quantity for m in movements), Decimal('0'))
    running_balance = trim.current_stock - total_delta
    for movement in movements:
        running_balance += movement.quantity
        movement.balance_after = running_balance

    movements.reverse()  # newest first for display

    context = {
        'active': 'inventory',
        'page_title': f'Stock Ledger - {trim.trim_name}',
        'trim': trim,
        'movements': movements,
    }
    return render(request, 'inventory/trim_stock_ledger.html', context)

@login_required
def production_issues(request):
    """List all production issues"""
    issues = ProductionIssue.objects.select_related('project', 'department', 'issued_by').all()
    
    context = {
        'active': 'inventory',
        'page_title': 'Production Issues',
        'issues': issues,
    }
    return render(request, 'inventory/production_issues.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_production_issue(request):
    """Add new production issue"""
    if request.method == 'POST':
        form = ProductionIssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.issued_by = request.user
            issue.save()
            
            # Handle issue details
            fabric_ids = request.POST.getlist('fabric_ids[]')
            fabric_roll_ids = request.POST.getlist('fabric_roll_ids[]')
            trim_ids = request.POST.getlist('trim_ids[]')
            quantities_issued = request.POST.getlist('quantities_issued[]')
            
            for i in range(len(quantities_issued)):
                if quantities_issued[i]:
                    detail = ProductionIssueDetail.objects.create(
                        production_issue=issue,
                        fabric_id=fabric_ids[i] if i < len(fabric_ids) and fabric_ids[i] else None,
                        fabric_roll_id=fabric_roll_ids[i] if i < len(fabric_roll_ids) and fabric_roll_ids[i] else None,
                        trim_id=trim_ids[i] if i < len(trim_ids) and trim_ids[i] else None,
                        quantity_issued=Decimal(quantities_issued[i]),
                        quantity_requested=Decimal(quantities_issued[i])
                    )
                    
                    # Update stock
                    if detail.fabric:
                        fabric = detail.fabric
                        fabric.current_stock -= detail.quantity_issued
                        fabric.save()
                        StockMovement.objects.create(
                            movement_type='issue',
                            reference_number=issue.issue_number,
                            reference_id=issue.pk,
                            fabric=fabric,
                            quantity=-detail.quantity_issued,
                            notes=f"Issued to production - {issue.project.project_number}",
                            created_by=request.user,
                        )
                    elif detail.trim:
                        trim = detail.trim
                        trim.current_stock -= int(detail.quantity_issued)
                        trim.save()
                        StockMovement.objects.create(
                            movement_type='issue',
                            reference_number=issue.issue_number,
                            reference_id=issue.pk,
                            trim=trim,
                            quantity=-detail.quantity_issued,
                            notes=f"Issued to production - {issue.project.project_number}",
                            created_by=request.user,
                        )

                    # Update fabric roll if used
                    if detail.fabric_roll:
                        roll = detail.fabric_roll
                        roll.used_length += detail.quantity_issued
                        roll.save()
            
            issue.status = 'issued'
            issue.save()
            
            messages.success(request, f'Production issue "{issue.issue_number}" created successfully!')
            return redirect('inventory:production_issues')
    else:
        form = ProductionIssueForm()
    
    context = {
        'active': 'inventory',
        'page_title': 'Add Production Issue',
        'form': form,
        'fabrics': Fabric.objects.filter(is_active=True),
        'fabric_rolls': FabricRoll.objects.filter(status='in_stock'),
        'trims': Trim.objects.filter(is_active=True),
    }
    return render(request, 'inventory/production_issue_form.html', context)

@login_required
def finished_goods_list(request):
    """List all finished goods"""
    finished_goods = FinishedGoods.objects.filter(is_active=True)

    # Search
    search = request.GET.get('search')
    if search:
        finished_goods = finished_goods.filter(
            Q(sku_code__icontains=search) |
            Q(size__icontains=search) |
            Q(color__icontains=search)
        )

    # Filter by stock status
    stock_status = request.GET.get('stock_status')
    if stock_status == 'low':
        finished_goods = finished_goods.filter(quantity_in_stock__gt=0, quantity_in_stock__lte=F('reorder_level'))
    elif stock_status == 'out':
        finished_goods = finished_goods.filter(quantity_in_stock=0)
    elif stock_status == 'normal':
        finished_goods = finished_goods.filter(quantity_in_stock__gt=F('reorder_level'))

    # Pagination
    paginator = Paginator(finished_goods, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'active': 'inventory',
        'page_title': 'Finished Goods',
        'finished_goods': page_obj,
        'search': search,
        'current_stock_status': stock_status,
    }
    return render(request, 'inventory/finished_goods.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_finished_goods(request):
    """Add new finished goods"""
    if request.method == 'POST':
        form = FinishedGoodsForm(request.POST)
        if form.is_valid():
            finished = form.save()
            messages.success(request, f'Finished goods "{finished.sku_code}" added successfully!')
            return redirect('inventory:finished_goods_list')
    else:
        form = FinishedGoodsForm()

    context = {
        'active': 'inventory',
        'page_title': 'Add Finished Goods',
        'form': form,
    }
    return render(request, 'inventory/finished_goods_form.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def edit_finished_goods(request, pk):
    """Edit finished goods"""
    finished = get_object_or_404(FinishedGoods, pk=pk)
    if request.method == 'POST':
        form = FinishedGoodsForm(request.POST, instance=finished)
        if form.is_valid():
            form.save()
            messages.success(request, f'Finished goods "{finished.sku_code}" updated successfully!')
            return redirect('inventory:finished_goods_list')
    else:
        form = FinishedGoodsForm(instance=finished)

    context = {
        'active': 'inventory',
        'page_title': 'Edit Finished Goods',
        'form': form,
        'finished_goods': finished,
    }
    return render(request, 'inventory/finished_goods_form.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_finished_goods_stock(request, pk):
    """
    Add stock to a finished goods item - e.g. a production batch just came
    off the line. Deliberately self-contained within Inventory: no style,
    buyer or supplier from another module is required.
    """
    finished = get_object_or_404(FinishedGoods, pk=pk)
    if request.method == 'POST':
        form = FinishedGoodsStockInForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            with transaction.atomic():
                FinishedGoods.objects.filter(pk=finished.pk).update(
                    quantity_in_stock=F('quantity_in_stock') + quantity,
                    quantity_produced=F('quantity_produced') + quantity,
                )
                movement = StockMovement.objects.create(
                    movement_type='production',
                    reference_number='',
                    reference_id=finished.pk,
                    finished_goods=finished,
                    quantity=quantity,
                    notes=form.cleaned_data['notes'],
                    created_by=request.user,
                )
                movement.reference_number = movement.movement_number
                movement.save(update_fields=['reference_number'])

            messages.success(request, f'Added {quantity} units to "{finished.sku_code}" stock.')
            return redirect('inventory:finished_goods_stock_ledger', pk=finished.pk)
    else:
        form = FinishedGoodsStockInForm()

    context = {
        'active': 'inventory',
        'page_title': 'Add Stock',
        'form': form,
        'finished_goods': finished,
    }
    return render(request, 'inventory/finished_goods_stock_in_form.html', context)

@login_required
def finished_goods_stock_ledger(request, pk):
    """
    All stock-affecting activity (Dispatches and Stock Adjustments) for a
    single finished goods item, newest first, with a running balance.
    """
    finished = get_object_or_404(FinishedGoods, pk=pk)
    movements = list(
        StockMovement.objects.filter(finished_goods=finished).order_by('movement_date', 'created_at')
    )

    total_delta = sum((m.quantity for m in movements), Decimal('0'))
    running_balance = Decimal(finished.quantity_in_stock) - total_delta
    for movement in movements:
        running_balance += movement.quantity
        movement.balance_after = running_balance

    movements.reverse()  # newest first for display

    context = {
        'active': 'inventory',
        'page_title': f'Stock Ledger - {finished.sku_code}',
        'finished_goods': finished,
        'movements': movements,
    }
    return render(request, 'inventory/finished_goods_stock_ledger.html', context)

@login_required
def dispatches(request):
    """List all dispatches"""
    dispatches = Dispatch.objects.select_related('project', 'project__buyer', 'created_by').all()
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        dispatches = dispatches.filter(status=status)
    
    context = {
        'active': 'inventory',
        'page_title': 'Dispatches',
        'dispatches': dispatches,
        'statuses': Dispatch._meta.get_field('status').choices,
        'current_status': status,
    }
    return render(request, 'inventory/dispatches.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_dispatch(request):
    """Add new dispatch"""
    if request.method == 'POST':
        form = DispatchForm(request.POST)
        if form.is_valid():
            dispatch = form.save(commit=False)
            dispatch.created_by = request.user
            dispatch.save()
            
            # Handle dispatch details
            finished_goods_ids = request.POST.getlist('finished_goods_ids[]')
            quantities = request.POST.getlist('quantities[]')
            carton_numbers = request.POST.getlist('carton_numbers[]')
            
            total_quantity = 0
            
            for i in range(len(quantities)):
                if quantities[i]:
                    detail = DispatchDetail.objects.create(
                        dispatch=dispatch,
                        finished_goods_id=finished_goods_ids[i] if i < len(finished_goods_ids) else None,
                        quantity=int(quantities[i]),
                        carton_number=carton_numbers[i] if i < len(carton_numbers) else f"CTN-{i+1:04d}"
                    )
                    
                    total_quantity += detail.quantity
                    
                    # Update finished goods stock
                    if detail.finished_goods:
                        fg = detail.finished_goods
                        fg.quantity_in_stock -= detail.quantity
                        fg.quantity_dispatched += detail.quantity
                        fg.save()
                        StockMovement.objects.create(
                            movement_type='dispatch',
                            reference_number=dispatch.dispatch_number,
                            reference_id=dispatch.pk,
                            finished_goods=fg,
                            quantity=-detail.quantity,
                            notes=f"Dispatched to {dispatch.project.buyer.buyer_name}",
                            created_by=request.user,
                        )
            
            dispatch.total_quantity = total_quantity
            dispatch.save()
            
            messages.success(request, f'Dispatch "{dispatch.dispatch_number}" created successfully!')
            return redirect('inventory:dispatches')
    else:
        form = DispatchForm()
    
    context = {
        'active': 'inventory',
        'page_title': 'Add Dispatch',
        'form': form,
        'finished_goods': FinishedGoods.objects.filter(is_active=True, quantity_in_stock__gt=0),
    }
    return render(request, 'inventory/dispatch_form.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def edit_dispatch(request, pk):
    """
    Edit a dispatch's header fields. Line items aren't editable here (they
    already moved finished-goods stock when created) and status changes go
    through update_dispatch_status instead, since 'shipped' needs approval.
    """
    dispatch = get_object_or_404(Dispatch, pk=pk)
    if request.method == 'POST':
        form = DispatchForm(request.POST, instance=dispatch)
        if form.is_valid():
            form.save()
            messages.success(request, f'Dispatch "{dispatch.dispatch_number}" updated successfully!')
            return redirect('inventory:dispatch_detail', pk=dispatch.pk)
    else:
        form = DispatchForm(instance=dispatch)

    context = {
        'active': 'inventory',
        'page_title': 'Edit Dispatch',
        'form': form,
        'dispatch': dispatch,
    }
    return render(request, 'inventory/dispatch_form.html', context)

@login_required
def dispatch_detail(request, pk):
    """Full view of a dispatch: header, line items, and status/shipment approval controls."""
    dispatch = get_object_or_404(
        Dispatch.objects.select_related(
            'project', 'project__buyer', 'created_by',
            'shipment_requested_by', 'shipment_approved_by',
        ),
        pk=pk,
    )
    context = {
        'active': 'inventory',
        'page_title': f'Dispatch {dispatch.dispatch_number}',
        'dispatch': dispatch,
        'items': dispatch.items.select_related('finished_goods'),
        'statuses': Dispatch.STATUS_CHOICES,
    }
    return render(request, 'inventory/dispatch_detail.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def update_dispatch_status(request, pk):
    """
    Update a dispatch's status. Setting it to 'Shipped' doesn't apply
    immediately - it creates a pending request that only a superuser can
    approve (approve_dispatch_shipment). Every other status applies right
    away. Once a Shipped request has been approved, the status is locked
    and this view refuses all further changes.
    """
    dispatch = get_object_or_404(Dispatch, pk=pk)
    if request.method == 'POST':
        if dispatch.is_status_locked:
            messages.error(request, "This dispatch was approved as Shipped and its status can no longer be changed.")
        else:
            new_status = request.POST.get('status')
            valid_statuses = dict(Dispatch.STATUS_CHOICES)
            if new_status not in valid_statuses:
                messages.error(request, "Invalid status.")
            elif new_status == 'shipped':
                dispatch.shipment_approval = 'pending'
                dispatch.shipment_requested_by = request.user
                dispatch.save(update_fields=['shipment_approval', 'shipment_requested_by'])
                messages.success(request, "Marking as Shipped submitted for approval - status will update once an admin approves it.")
            else:
                dispatch.status = new_status
                dispatch.save(update_fields=['status'])
                messages.success(request, f'Status updated to "{valid_statuses[new_status]}".')
    return redirect('inventory:dispatch_detail', pk=dispatch.pk)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_dispatch_shipment(request, pk):
    """Approve a pending 'Shipped' request - this locks the status permanently."""
    dispatch = get_object_or_404(Dispatch, pk=pk)
    if request.method == 'POST' and dispatch.shipment_approval == 'pending':
        dispatch.status = 'shipped'
        dispatch.shipment_approval = 'approved'
        dispatch.shipment_approved_by = request.user
        dispatch.shipment_approved_date = date.today()
        dispatch.save(update_fields=['status', 'shipment_approval', 'shipment_approved_by', 'shipment_approved_date'])
        messages.success(request, f'Dispatch "{dispatch.dispatch_number}" approved as Shipped - status is now locked.')
    return redirect('inventory:dispatch_detail', pk=dispatch.pk)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_dispatch_shipment(request, pk):
    """Reject a pending 'Shipped' request - status stays whatever it was, and can be requested again later."""
    dispatch = get_object_or_404(Dispatch, pk=pk)
    if request.method == 'POST' and dispatch.shipment_approval == 'pending':
        dispatch.shipment_approval = 'rejected'
        dispatch.shipment_approved_by = request.user
        dispatch.shipment_approved_date = date.today()
        dispatch.save(update_fields=['shipment_approval', 'shipment_approved_by', 'shipment_approved_date'])
        messages.success(request, f'Shipped request for "{dispatch.dispatch_number}" rejected.')
    return redirect('inventory:dispatch_detail', pk=dispatch.pk)

@login_required
def stock_adjustments(request):
    """List all stock adjustments"""
    adjustments = StockAdjustment.objects.select_related('created_by', 'approved_by').prefetch_related('details').all()

    context = {
        'active': 'inventory',
        'page_title': 'Stock Adjustments',
        'adjustments': adjustments,
    }
    return render(request, 'inventory/stock_adjustments.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_stock_adjustment(request):
    """
    Request a stock adjustment. This no longer applies immediately - it's
    created as 'pending' and only actually changes stock once a superuser
    approves it (see approve_stock_adjustment / _apply_stock_adjustment).
    """
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            adjustment = form.save(commit=False)
            adjustment.status = 'pending'
            adjustment.created_by = request.user
            adjustment.save()
            messages.success(
                request,
                f'Stock adjustment "{adjustment.adjustment_number}" submitted for approval - '
                'stock will update once an admin approves it.'
            )
            return redirect('inventory:stock_adjustments')
    else:
        form = StockAdjustmentForm()

    context = {
        'active': 'inventory',
        'page_title': 'Add Stock Adjustment',
        'form': form,
        'fabrics': Fabric.objects.filter(is_active=True),
        'trims': Trim.objects.filter(is_active=True),
        'finished_goods': FinishedGoods.objects.filter(is_active=True),
    }
    return render(request, 'inventory/stock_adjustment_form.html', context)

def _apply_stock_adjustment(adjustment):
    """
    Apply an approved StockAdjustment's stock effects. Must be called
    inside a transaction.atomic() block by the caller. Raises ValueError
    (caller should catch it) if there isn't enough stock/lot quantity to
    carry out a decrease.

    Two shapes:
    - Lot-wise (has StockAdjustmentDetail rows, Fabric only): moves each
      named lot's used_length and the parent Fabric's current_stock.
    - Single-target (no detail rows - Finished Goods, Trim, or a plain
      non-lot Fabric correction): moves the one fabric/trim/finished_goods
      target by adjustment.quantity. This is the original add_stock_adjustment
      logic, just relocated so it can be reused from the approval view.
    """
    details = list(adjustment.details.select_related('fabric_roll').all())

    if details:
        fabric = Fabric.objects.select_for_update().get(pk=adjustment.fabric_id)
        total_qty = sum((d.quantity for d in details), Decimal('0'))
        if adjustment.direction == 'decrease' and total_qty > fabric.current_stock:
            raise ValueError(
                f"Can't decrease stock by {total_qty}: only {fabric.current_stock} in stock."
            )
        for detail in details:
            roll = FabricRoll.objects.select_for_update().get(pk=detail.fabric_roll_id)
            if adjustment.direction == 'decrease':
                if detail.quantity > roll.remaining_length:
                    raise ValueError(
                        f"Can't take {detail.quantity} from lot {roll.lot_number}: "
                        f"only {roll.remaining_length} remaining."
                    )
                roll.used_length += detail.quantity
            else:
                if detail.quantity > roll.used_length:
                    raise ValueError(
                        f"Can't increase lot {roll.lot_number} by {detail.quantity}: "
                        f"only {roll.used_length} previously issued from it."
                    )
                roll.used_length -= detail.quantity
            roll.save()

        signed_total = total_qty if adjustment.direction == 'increase' else -total_qty
        fabric.current_stock += signed_total
        fabric.save(update_fields=['current_stock'])

        StockMovement.objects.create(
            movement_type='issue' if adjustment.adjustment_type == 'issue' else 'adjustment',
            reference_number=adjustment.adjustment_number,
            reference_id=adjustment.pk,
            fabric=fabric,
            quantity=signed_total,
            notes=adjustment.reason,
            created_by=adjustment.approved_by,
        )
    else:
        quantity = adjustment.quantity
        signed_quantity = quantity if adjustment.direction == 'increase' else -quantity

        if adjustment.fabric_id:
            fabric = Fabric.objects.select_for_update().get(pk=adjustment.fabric_id)
            if adjustment.direction == 'decrease' and quantity > fabric.current_stock:
                raise ValueError(f"Can't decrease stock by {quantity}: only {fabric.current_stock} in stock.")
            fabric.current_stock += signed_quantity
            fabric.save(update_fields=['current_stock'])
        elif adjustment.trim_id:
            trim = Trim.objects.select_for_update().get(pk=adjustment.trim_id)
            if adjustment.direction == 'decrease' and quantity > trim.current_stock:
                raise ValueError(f"Can't decrease stock by {quantity}: only {trim.current_stock} in stock.")
            trim.current_stock += int(signed_quantity)
            trim.save(update_fields=['current_stock'])
        elif adjustment.finished_goods_id:
            fg = FinishedGoods.objects.select_for_update().get(pk=adjustment.finished_goods_id)
            if adjustment.direction == 'decrease' and quantity > fg.quantity_in_stock:
                raise ValueError(f"Can't decrease stock by {quantity}: only {fg.quantity_in_stock} in stock.")
            fg.quantity_in_stock += int(signed_quantity)
            fg.save(update_fields=['quantity_in_stock'])

        StockMovement.objects.create(
            movement_type='adjustment',
            reference_number=adjustment.adjustment_number,
            reference_id=adjustment.pk,
            fabric_id=adjustment.fabric_id,
            trim_id=adjustment.trim_id,
            finished_goods_id=adjustment.finished_goods_id,
            quantity=signed_quantity,
            notes=adjustment.reason,
            created_by=adjustment.approved_by,
        )

@login_required
@user_passes_test(lambda u: u.is_superuser)
def pending_adjustments(request):
    """
    Everything awaiting superuser approval across the warehouse: Stock
    Adjustments, Dispatch shipments, Machine sold/scrapped requests, and
    Supply (Spare Part/Stationery) Adjustments - superuser only.
    """
    adjustments = StockAdjustment.objects.filter(status='pending').select_related(
        'fabric', 'trim', 'finished_goods', 'created_by'
    ).prefetch_related('details__fabric_roll')

    dispatch_shipments = Dispatch.objects.filter(shipment_approval='pending').select_related(
        'project', 'project__buyer', 'shipment_requested_by'
    )

    machine_events = MachineEvent.objects.filter(status='pending').select_related(
        'machine', 'created_by'
    )

    supply_adjustments_pending = SupplyAdjustment.objects.filter(status='pending').select_related(
        'spare_part', 'stationery_item', 'created_by'
    )

    context = {
        'active': 'inventory',
        'page_title': 'Pending Approvals',
        'adjustments': adjustments,
        'dispatch_shipments': dispatch_shipments,
        'machine_events': machine_events,
        'supply_adjustments_pending': supply_adjustments_pending,
    }
    return render(request, 'inventory/pending_adjustments.html', context)

@login_required
def stock_adjustment_detail(request, pk):
    """Review page for a single stock adjustment, including its lot breakdown if any."""
    adjustment = get_object_or_404(
        StockAdjustment.objects.select_related(
            'fabric', 'trim', 'finished_goods', 'purchase_order', 'created_by', 'approved_by'
        ).prefetch_related('details__fabric_roll'),
        pk=pk,
    )
    context = {
        'active': 'inventory',
        'page_title': f'Adjustment {adjustment.adjustment_number}',
        'adjustment': adjustment,
    }
    return render(request, 'inventory/stock_adjustment_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_stock_adjustment(request, pk):
    """Approve a pending adjustment - this is the only place stock actually changes."""
    adjustment = get_object_or_404(StockAdjustment, pk=pk)
    if request.method == 'POST' and adjustment.status == 'pending':
        try:
            with transaction.atomic():
                adjustment.approved_by = request.user
                adjustment.approved_date = date.today()
                _apply_stock_adjustment(adjustment)
                adjustment.status = 'approved'
                adjustment.save(update_fields=['status', 'approved_by', 'approved_date'])
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f'Adjustment "{adjustment.adjustment_number}" approved - stock updated.')
    return redirect('inventory:pending_adjustments')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_stock_adjustment(request, pk):
    """Reject a pending adjustment - no stock change."""
    adjustment = get_object_or_404(StockAdjustment, pk=pk)
    if request.method == 'POST' and adjustment.status == 'pending':
        form = RejectStockAdjustmentForm(request.POST)
        if form.is_valid():
            adjustment.status = 'rejected'
            adjustment.rejection_reason = form.cleaned_data['rejection_reason']
            adjustment.approved_by = request.user
            adjustment.approved_date = date.today()
            adjustment.save(update_fields=['status', 'rejection_reason', 'approved_by', 'approved_date'])
            messages.success(request, f'Adjustment "{adjustment.adjustment_number}" rejected.')
        else:
            messages.error(request, "A rejection reason is required.")
    return redirect('inventory:pending_adjustments')

TOP_N = 10

def _fabric_report_rows(queryset):
    return [{
        'code': fabric.fabric_code,
        'name': fabric.fabric_name,
        'color': fabric.color,
        'stock': fabric.current_stock,
        'min_stock': fabric.min_stock,
        'status': fabric.stock_status,
    } for fabric in queryset]

def _trim_report_rows(queryset):
    return [{
        'code': trim.trim_code,
        'name': trim.trim_name,
        'stock': trim.current_stock,
        'reorder_level': trim.reorder_level,
        'status': trim.stock_status,
    } for trim in queryset]

def _finished_goods_report_rows(queryset):
    return [{
        'sku': fg.sku_code,
        'size': fg.size,
        'color': fg.color,
        'in_stock': fg.quantity_in_stock,
        'dispatched': fg.quantity_dispatched,
        'status': 'low' if fg.is_low_stock else 'normal',
    } for fg in queryset]

@login_required
def stock_report(request):
    """
    Stock report overview - top 10 most recently updated items per
    category, with a 'View All' link to the full paginated/searchable
    list page and PDF/Excel export of the complete data.
    """
    fabrics = Fabric.objects.filter(is_active=True)
    trims = Trim.objects.filter(is_active=True)
    finished = FinishedGoods.objects.filter(is_active=True)

    context = {
        'active': 'inventory',
        'page_title': 'Stock Report',
        'fabric_data': _fabric_report_rows(fabrics.order_by('-updated_at')[:TOP_N]),
        'trim_data': _trim_report_rows(trims.order_by('-updated_at')[:TOP_N]),
        'finished_data': _finished_goods_report_rows(finished.order_by('-updated_at')[:TOP_N]),
        'fabric_total': fabrics.count(),
        'trim_total': trims.count(),
        'finished_total': finished.count(),
        'top_n': TOP_N,
    }
    return render(request, 'inventory/stock_report.html', context)

@login_required
def stock_report_export_excel(request):
    """Full (untruncated) stock report as a 3-sheet Excel workbook."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = Workbook()
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill('solid', start_color='4472C4')
    header_align = Alignment(horizontal='center')

    def write_sheet(ws, headers, rows):
        for col, title in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=title)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align
        for row_idx, row in enumerate(rows, start=2):
            for col_idx, value in enumerate(row, start=1):
                ws.cell(row=row_idx, column=col_idx, value=value)
        for col in range(1, len(headers) + 1):
            ws.column_dimensions[chr(64 + col)].width = 18

    ws_fabric = wb.active
    ws_fabric.title = 'Fabrics'
    write_sheet(
        ws_fabric,
        ['Code', 'Name', 'Color', 'Stock', 'Min Stock', 'Status'],
        [(f.fabric_code, f.fabric_name, f.color, float(f.current_stock), float(f.min_stock), f.stock_status)
         for f in Fabric.objects.filter(is_active=True)],
    )

    ws_trim = wb.create_sheet('Trims')
    write_sheet(
        ws_trim,
        ['Code', 'Name', 'Stock', 'Reorder Level', 'Status'],
        [(t.trim_code, t.trim_name, t.current_stock, t.reorder_level, t.stock_status)
         for t in Trim.objects.filter(is_active=True)],
    )

    ws_fg = wb.create_sheet('Finished Goods')
    write_sheet(
        ws_fg,
        ['SKU', 'Size', 'Color', 'In Stock', 'Dispatched', 'Status'],
        [(fg.sku_code, fg.size, fg.color, fg.quantity_in_stock, fg.quantity_dispatched,
          'Low' if fg.is_low_stock else 'Normal')
         for fg in FinishedGoods.objects.filter(is_active=True)],
    )

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="stock_report_{date.today():%Y%m%d}.xlsx"'
    wb.save(response)
    return response

@login_required
def stock_report_export_pdf(request):
    """Full (untruncated) stock report as a landscape PDF, one table per category."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="stock_report_{date.today():%Y%m%d}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4),
                             leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    elements = [Paragraph('Stock Report', styles['Title']), Spacer(1, 0.5 * cm)]

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])

    def add_section(title, headers, rows):
        elements.append(Paragraph(title, styles['Heading2']))
        data = [headers] + [[str(v) for v in row] for row in rows]
        table = Table(data, repeatRows=1)
        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 0.7 * cm))

    add_section(
        'Fabrics',
        ['Code', 'Name', 'Color', 'Stock', 'Min Stock', 'Status'],
        [(f.fabric_code, f.fabric_name, f.color, f.current_stock, f.min_stock, f.stock_status)
         for f in Fabric.objects.filter(is_active=True)],
    )
    add_section(
        'Trims',
        ['Code', 'Name', 'Stock', 'Reorder Level', 'Status'],
        [(t.trim_code, t.trim_name, t.current_stock, t.reorder_level, t.stock_status)
         for t in Trim.objects.filter(is_active=True)],
    )
    add_section(
        'Finished Goods',
        ['SKU', 'Size', 'Color', 'In Stock', 'Dispatched', 'Status'],
        [(fg.sku_code, fg.size, fg.color, fg.quantity_in_stock, fg.quantity_dispatched,
          'Low' if fg.is_low_stock else 'Normal')
         for fg in FinishedGoods.objects.filter(is_active=True)],
    )

    doc.build(elements)
    return response

# =============================================================== machines

@login_required
def machine_list(request):
    """List all machines"""
    machines = Machine.objects.select_related('department', 'supplier')

    search = request.GET.get('search')
    if search:
        machines = machines.filter(
            Q(machine_code__icontains=search) |
            Q(machine_name__icontains=search) |
            Q(brand__icontains=search) |
            Q(serial_number__icontains=search)
        )

    machine_type = request.GET.get('type')
    if machine_type:
        machines = machines.filter(machine_type=machine_type)

    status = request.GET.get('status')
    if status:
        machines = machines.filter(status=status)

    department_id = request.GET.get('department')
    if department_id:
        machines = machines.filter(department_id=department_id)

    paginator = Paginator(machines, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    from apps.hr.models import Department
    context = {
        'active': 'inventory',
        'page_title': 'Machines',
        'machines': page_obj,
        'machine_types': Machine.MACHINE_TYPES,
        'statuses': Machine.STATUS_CHOICES,
        'departments': Department.objects.all(),
        'search': search,
        'current_type': machine_type,
        'current_status': status,
        'current_department': department_id,
    }
    return render(request, 'inventory/machine_list.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_machine(request):
    """Add new machine"""
    if request.method == 'POST':
        form = MachineForm(request.POST)
        if form.is_valid():
            machine = form.save(commit=False)
            machine.created_by = request.user
            machine.save()
            messages.success(request, f'Machine "{machine.machine_code}" added successfully!')
            return redirect('inventory:machine_list')
    else:
        form = MachineForm()

    context = {
        'active': 'inventory',
        'page_title': 'Add Machine',
        'form': form,
    }
    return render(request, 'inventory/machine_form.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def edit_machine(request, pk):
    """Edit machine"""
    machine = get_object_or_404(Machine, pk=pk)
    if request.method == 'POST':
        form = MachineForm(request.POST, instance=machine)
        if form.is_valid():
            form.save()
            messages.success(request, f'Machine "{machine.machine_code}" updated successfully!')
            return redirect('inventory:machine_detail', pk=machine.pk)
    else:
        form = MachineForm(instance=machine)

    context = {
        'active': 'inventory',
        'page_title': 'Edit Machine',
        'form': form,
        'machine': machine,
    }
    return render(request, 'inventory/machine_form.html', context)

@login_required
def machine_detail(request, pk):
    """Machine detail: info + event timeline + recent spare-part consumption against it."""
    machine = get_object_or_404(Machine.objects.select_related('department', 'supplier'), pk=pk)
    context = {
        'active': 'inventory',
        'page_title': f'{machine.machine_code} - {machine.machine_name}',
        'machine': machine,
        'events': machine.events.select_related('created_by', 'approved_by'),
        'spare_part_consumptions': machine.spare_part_consumptions.select_related(
            'spare_part', 'department'
        ).order_by('-consumption_date')[:20],
    }
    return render(request, 'inventory/machine_detail.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_machine_event(request, pk):
    """
    Log an event against a machine. 'Sold'/'Scrapped' are created as
    pending and don't change Machine.status until a superuser approves
    them (approve_machine_event) - mirrors Dispatch.shipment_approval.
    Every other event type applies immediately and updates Machine.status
    to match.
    """
    machine = get_object_or_404(Machine, pk=pk)
    if request.method == 'POST':
        form = MachineEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.machine = machine
            event.created_by = request.user

            if event.event_type in ('sold', 'scrapped'):
                event.status = 'pending'
                event.save()
                messages.success(
                    request,
                    f'"{event.get_event_type_display()}" submitted for approval - '
                    'the machine stays active until an admin approves it.'
                )
            else:
                event.status = 'approved'
                event.approved_by = request.user
                event.approved_date = date.today()
                event.save()

                status_map = {
                    'breakdown': 'broken_down',
                    'repair_started': 'under_maintenance',
                    'repair_completed': 'active',
                    'maintenance': 'under_maintenance',
                }
                new_status = status_map.get(event.event_type)
                if new_status and new_status != machine.status:
                    machine.status = new_status
                    machine.save(update_fields=['status'])

                messages.success(request, f'"{event.get_event_type_display()}" logged for {machine.machine_code}.')

            return redirect('inventory:machine_detail', pk=machine.pk)
    else:
        form = MachineEventForm()

    context = {
        'active': 'inventory',
        'page_title': f'Log Event - {machine.machine_code}',
        'form': form,
        'machine': machine,
    }
    return render(request, 'inventory/machine_event_form.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_machine_event(request, pk, event_pk):
    """Approve a pending Sold/Scrapped request - this is the only place Machine.status becomes sold/scrapped."""
    machine = get_object_or_404(Machine, pk=pk)
    event = get_object_or_404(MachineEvent, pk=event_pk, machine=machine)
    if request.method == 'POST' and event.status == 'pending':
        event.status = 'approved'
        event.approved_by = request.user
        event.approved_date = date.today()
        event.save(update_fields=['status', 'approved_by', 'approved_date'])

        machine.status = event.event_type  # 'sold'/'scrapped' match Machine.STATUS_CHOICES exactly
        machine.save(update_fields=['status'])

        messages.success(request, f'"{event.get_event_type_display()}" approved for {machine.machine_code}.')
    return redirect('inventory:machine_detail', pk=machine.pk)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_machine_event(request, pk, event_pk):
    """Reject a pending Sold/Scrapped request - Machine.status is untouched."""
    machine = get_object_or_404(Machine, pk=pk)
    event = get_object_or_404(MachineEvent, pk=event_pk, machine=machine)
    if request.method == 'POST' and event.status == 'pending':
        form = RejectMachineEventForm(request.POST)
        if form.is_valid():
            event.status = 'rejected'
            event.rejection_reason = form.cleaned_data['rejection_reason']
            event.approved_by = request.user
            event.approved_date = date.today()
            event.save(update_fields=['status', 'rejection_reason', 'approved_by', 'approved_date'])
            messages.success(request, f'"{event.get_event_type_display()}" request rejected.')
        else:
            messages.error(request, "A rejection reason is required.")
    return redirect('inventory:machine_detail', pk=machine.pk)

# ============================================================= spare parts

@login_required
def spare_part_list(request):
    """List all spare parts"""
    parts = SparePart.objects.filter(is_active=True).select_related('supplier')

    search = request.GET.get('search')
    if search:
        parts = parts.filter(Q(part_name__icontains=search))

    category = request.GET.get('category')
    if category:
        parts = parts.filter(category=category)

    stock_status = request.GET.get('stock_status')
    if stock_status == 'low':
        parts = parts.filter(current_stock__lte=F('min_stock'))
    elif stock_status == 'normal':
        parts = parts.filter(current_stock__gt=F('min_stock'), current_stock__lt=F('max_stock'))
    elif stock_status == 'overstock':
        parts = parts.filter(current_stock__gte=F('max_stock'))

    paginator = Paginator(parts, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'active': 'inventory',
        'page_title': 'Spare Parts',
        'spare_parts': page_obj,
        'categories': SparePart.CATEGORY_CHOICES,
        'search': search,
        'current_category': category,
        'current_stock_status': stock_status,
    }
    return render(request, 'inventory/spare_part_list.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_spare_part(request):
    """Add new spare part"""
    if request.method == 'POST':
        form = SparePartForm(request.POST)
        if form.is_valid():
            part = form.save()
            messages.success(request, f'Spare part "{part.part_name}" added successfully!')
            return redirect('inventory:spare_part_list')
    else:
        form = SparePartForm()

    context = {'active': 'inventory', 'page_title': 'Add Spare Part', 'form': form}
    return render(request, 'inventory/spare_part_form.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def edit_spare_part(request, pk):
    """Edit spare part"""
    part = get_object_or_404(SparePart, pk=pk)
    if request.method == 'POST':
        form = SparePartForm(request.POST, instance=part)
        if form.is_valid():
            form.save()
            messages.success(request, f'Spare part "{part.part_name}" updated successfully!')
            return redirect('inventory:spare_part_list')
    else:
        form = SparePartForm(instance=part)

    context = {'active': 'inventory', 'page_title': 'Edit Spare Part', 'form': form, 'spare_part': part}
    return render(request, 'inventory/spare_part_form.html', context)

@login_required
def spare_part_stock_ledger(request, pk):
    """All stock-affecting activity for a single spare part, newest first, with a running balance."""
    part = get_object_or_404(SparePart, pk=pk)
    movements = list(StockMovement.objects.filter(spare_part=part).order_by('movement_date', 'created_at'))

    total_delta = sum((m.quantity for m in movements), Decimal('0'))
    running_balance = Decimal(part.current_stock) - total_delta
    for movement in movements:
        running_balance += movement.quantity
        movement.balance_after = running_balance
    movements.reverse()

    context = {
        'active': 'inventory',
        'page_title': f'Stock Ledger - {part.part_name}',
        'spare_part': part,
        'movements': movements,
        'consumptions': part.consumptions.select_related('department', 'machine').order_by('-consumption_date')[:20],
    }
    return render(request, 'inventory/spare_part_stock_ledger.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_spare_part_stock(request, pk):
    """Add stock to a spare part - immediate, no approval (mirrors add_trim_stock)."""
    part = get_object_or_404(SparePart, pk=pk)
    if request.method == 'POST':
        form = SparePartStockInForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            with transaction.atomic():
                SparePart.objects.filter(pk=part.pk).update(current_stock=F('current_stock') + quantity)
                movement = StockMovement.objects.create(
                    movement_type='receipt', reference_number='', reference_id=part.pk,
                    spare_part=part, quantity=quantity,
                    notes=form.cleaned_data['notes'], created_by=request.user,
                )
                movement.reference_number = movement.movement_number
                movement.save(update_fields=['reference_number'])
            messages.success(request, f'Added {quantity} units to "{part.part_name}" stock.')
            return redirect('inventory:spare_part_stock_ledger', pk=part.pk)
    else:
        form = SparePartStockInForm()

    context = {'active': 'inventory', 'page_title': 'Add Stock', 'form': form, 'spare_part': part}
    return render(request, 'inventory/spare_part_stock_in_form.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def record_spare_part_consumption(request, pk):
    """
    Record a department's (optionally machine-linked) use of a spare part.
    Immediate - not approval-gated, this is routine maintenance logging,
    not a correction (see SupplyAdjustment for corrections).
    """
    part = get_object_or_404(SparePart, pk=pk)
    if request.method == 'POST':
        form = SparePartConsumptionForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            if quantity > part.current_stock:
                messages.error(request, f"Can't consume {quantity}: only {part.current_stock} in stock.")
            else:
                department = form.cleaned_data['department']
                with transaction.atomic():
                    SparePartConsumption.objects.create(
                        spare_part=part,
                        department=department,
                        machine=form.cleaned_data['machine'],
                        quantity=quantity,
                        unit_price_at_consumption=part.unit_price,
                        consumption_date=form.cleaned_data['consumption_date'],
                        notes=form.cleaned_data['notes'],
                        issued_by=request.user,
                    )
                    SparePart.objects.filter(pk=part.pk).update(current_stock=F('current_stock') - quantity)
                    movement = StockMovement.objects.create(
                        movement_type='issue', reference_number='', reference_id=part.pk,
                        spare_part=part, quantity=-quantity,
                        notes=f"Issued to {department.name}", created_by=request.user,
                    )
                    movement.reference_number = movement.movement_number
                    movement.save(update_fields=['reference_number'])
                messages.success(request, f'Recorded consumption of {quantity} units of "{part.part_name}".')
                return redirect('inventory:spare_part_stock_ledger', pk=part.pk)
    else:
        form = SparePartConsumptionForm()

    context = {'active': 'inventory', 'page_title': 'Record Consumption', 'form': form, 'spare_part': part}
    return render(request, 'inventory/spare_part_consumption_form.html', context)

# ============================================================== stationery

@login_required
def stationery_list(request):
    """List all stationery items"""
    items = StationeryItem.objects.filter(is_active=True)

    search = request.GET.get('search')
    if search:
        items = items.filter(Q(item_name__icontains=search))

    category = request.GET.get('category')
    if category:
        items = items.filter(category=category)

    stock_status = request.GET.get('stock_status')
    if stock_status == 'low':
        items = items.filter(current_stock__lte=F('min_stock'))
    elif stock_status == 'normal':
        items = items.filter(current_stock__gt=F('min_stock'), current_stock__lt=F('max_stock'))
    elif stock_status == 'overstock':
        items = items.filter(current_stock__gte=F('max_stock'))

    paginator = Paginator(items, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'active': 'inventory',
        'page_title': 'Stationery',
        'stationery_items': page_obj,
        'categories': StationeryItem.CATEGORY_CHOICES,
        'search': search,
        'current_category': category,
        'current_stock_status': stock_status,
    }
    return render(request, 'inventory/stationery_list.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_stationery_item(request):
    """Add new stationery item"""
    if request.method == 'POST':
        form = StationeryItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            messages.success(request, f'Stationery item "{item.item_name}" added successfully!')
            return redirect('inventory:stationery_list')
    else:
        form = StationeryItemForm()

    context = {'active': 'inventory', 'page_title': 'Add Stationery Item', 'form': form}
    return render(request, 'inventory/stationery_form.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def edit_stationery_item(request, pk):
    """Edit stationery item"""
    item = get_object_or_404(StationeryItem, pk=pk)
    if request.method == 'POST':
        form = StationeryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'Stationery item "{item.item_name}" updated successfully!')
            return redirect('inventory:stationery_list')
    else:
        form = StationeryItemForm(instance=item)

    context = {'active': 'inventory', 'page_title': 'Edit Stationery Item', 'form': form, 'stationery_item': item}
    return render(request, 'inventory/stationery_form.html', context)

@login_required
def stationery_stock_ledger(request, pk):
    """All stock-affecting activity for a single stationery item, newest first, with a running balance."""
    item = get_object_or_404(StationeryItem, pk=pk)
    movements = list(StockMovement.objects.filter(stationery_item=item).order_by('movement_date', 'created_at'))

    total_delta = sum((m.quantity for m in movements), Decimal('0'))
    running_balance = Decimal(item.current_stock) - total_delta
    for movement in movements:
        running_balance += movement.quantity
        movement.balance_after = running_balance
    movements.reverse()

    context = {
        'active': 'inventory',
        'page_title': f'Stock Ledger - {item.item_name}',
        'stationery_item': item,
        'movements': movements,
        'consumptions': item.consumptions.select_related('department').order_by('-consumption_date')[:20],
    }
    return render(request, 'inventory/stationery_stock_ledger.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_stationery_stock(request, pk):
    """Add stock to a stationery item - immediate, no approval."""
    item = get_object_or_404(StationeryItem, pk=pk)
    if request.method == 'POST':
        form = StationeryStockInForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            with transaction.atomic():
                StationeryItem.objects.filter(pk=item.pk).update(current_stock=F('current_stock') + quantity)
                movement = StockMovement.objects.create(
                    movement_type='receipt', reference_number='', reference_id=item.pk,
                    stationery_item=item, quantity=quantity,
                    notes=form.cleaned_data['notes'], created_by=request.user,
                )
                movement.reference_number = movement.movement_number
                movement.save(update_fields=['reference_number'])
            messages.success(request, f'Added {quantity} units to "{item.item_name}" stock.')
            return redirect('inventory:stationery_stock_ledger', pk=item.pk)
    else:
        form = StationeryStockInForm()

    context = {'active': 'inventory', 'page_title': 'Add Stock', 'form': form, 'stationery_item': item}
    return render(request, 'inventory/stationery_stock_in_form.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def record_stationery_consumption(request, pk):
    """Record a department's use of a stationery item - immediate, not approval-gated."""
    item = get_object_or_404(StationeryItem, pk=pk)
    if request.method == 'POST':
        form = StationeryConsumptionForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            if quantity > item.current_stock:
                messages.error(request, f"Can't consume {quantity}: only {item.current_stock} in stock.")
            else:
                department = form.cleaned_data['department']
                with transaction.atomic():
                    StationeryConsumption.objects.create(
                        stationery_item=item,
                        department=department,
                        quantity=quantity,
                        unit_price_at_consumption=item.unit_price,
                        consumption_date=form.cleaned_data['consumption_date'],
                        notes=form.cleaned_data['notes'],
                        issued_by=request.user,
                    )
                    StationeryItem.objects.filter(pk=item.pk).update(current_stock=F('current_stock') - quantity)
                    movement = StockMovement.objects.create(
                        movement_type='issue', reference_number='', reference_id=item.pk,
                        stationery_item=item, quantity=-quantity,
                        notes=f"Issued to {department.name}", created_by=request.user,
                    )
                    movement.reference_number = movement.movement_number
                    movement.save(update_fields=['reference_number'])
                messages.success(request, f'Recorded consumption of {quantity} units of "{item.item_name}".')
                return redirect('inventory:stationery_stock_ledger', pk=item.pk)
    else:
        form = StationeryConsumptionForm()

    context = {'active': 'inventory', 'page_title': 'Record Consumption', 'form': form, 'stationery_item': item}
    return render(request, 'inventory/stationery_consumption_form.html', context)

# ========================================================= supply adjustments

@login_required
def supply_adjustments(request):
    """List all supply adjustments (Spare Parts + Stationery)"""
    adjustments = SupplyAdjustment.objects.select_related(
        'spare_part', 'stationery_item', 'created_by', 'approved_by'
    )
    context = {
        'active': 'inventory',
        'page_title': 'Supply Adjustments',
        'adjustments': adjustments,
    }
    return render(request, 'inventory/supply_adjustments.html', context)

@login_required
@user_passes_test(is_inventory_or_admin)
def add_supply_adjustment(request):
    """Request a correction for a Spare Part or Stationery Item - pending until a superuser approves it."""
    if request.method == 'POST':
        form = SupplyAdjustmentForm(request.POST)
        if form.is_valid():
            adjustment = form.save(commit=False)
            adjustment.status = 'pending'
            adjustment.created_by = request.user
            adjustment.save()
            messages.success(
                request,
                f'Adjustment "{adjustment.adjustment_number}" submitted for approval - '
                'stock will update once an admin approves it.'
            )
            return redirect('inventory:supply_adjustments')
    else:
        form = SupplyAdjustmentForm()

    context = {
        'active': 'inventory',
        'page_title': 'Add Supply Adjustment',
        'form': form,
    }
    return render(request, 'inventory/supply_adjustment_form.html', context)

def _apply_supply_adjustment(adjustment):
    """
    Apply an approved SupplyAdjustment's stock effect. Must be called
    inside a transaction.atomic() block by the caller. Mirrors
    _apply_stock_adjustment's single-target branch.
    """
    quantity = adjustment.quantity
    signed_quantity = quantity if adjustment.direction == 'increase' else -quantity

    if adjustment.spare_part_id:
        part = SparePart.objects.select_for_update().get(pk=adjustment.spare_part_id)
        if adjustment.direction == 'decrease' and quantity > part.current_stock:
            raise ValueError(f"Can't decrease stock by {quantity}: only {part.current_stock} in stock.")
        part.current_stock += signed_quantity
        part.save(update_fields=['current_stock'])
    elif adjustment.stationery_item_id:
        item = StationeryItem.objects.select_for_update().get(pk=adjustment.stationery_item_id)
        if adjustment.direction == 'decrease' and quantity > item.current_stock:
            raise ValueError(f"Can't decrease stock by {quantity}: only {item.current_stock} in stock.")
        item.current_stock += signed_quantity
        item.save(update_fields=['current_stock'])

    StockMovement.objects.create(
        movement_type='adjustment',
        reference_number=adjustment.adjustment_number,
        reference_id=adjustment.pk,
        spare_part_id=adjustment.spare_part_id,
        stationery_item_id=adjustment.stationery_item_id,
        quantity=signed_quantity,
        notes=adjustment.reason,
        created_by=adjustment.approved_by,
    )

@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_supply_adjustment(request, pk):
    """Approve a pending supply adjustment - this is the only place stock actually changes."""
    adjustment = get_object_or_404(SupplyAdjustment, pk=pk)
    if request.method == 'POST' and adjustment.status == 'pending':
        try:
            with transaction.atomic():
                adjustment.approved_by = request.user
                adjustment.approved_date = date.today()
                _apply_supply_adjustment(adjustment)
                adjustment.status = 'approved'
                adjustment.save(update_fields=['status', 'approved_by', 'approved_date'])
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f'Adjustment "{adjustment.adjustment_number}" approved - stock updated.')
    return redirect('inventory:supply_adjustments')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_supply_adjustment(request, pk):
    """Reject a pending supply adjustment - no stock change."""
    adjustment = get_object_or_404(SupplyAdjustment, pk=pk)
    if request.method == 'POST' and adjustment.status == 'pending':
        form = RejectSupplyAdjustmentForm(request.POST)
        if form.is_valid():
            adjustment.status = 'rejected'
            adjustment.rejection_reason = form.cleaned_data['rejection_reason']
            adjustment.approved_by = request.user
            adjustment.approved_date = date.today()
            adjustment.save(update_fields=['status', 'rejection_reason', 'approved_by', 'approved_date'])
            messages.success(request, f'Adjustment "{adjustment.adjustment_number}" rejected.')
        else:
            messages.error(request, "A rejection reason is required.")
    return redirect('inventory:supply_adjustments')