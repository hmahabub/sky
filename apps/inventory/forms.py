from django import forms
from .models import (
    Fabric, FabricRoll, Trim, GoodsReceipt, GoodsReceiptDetail,
    TrimReceipt, TrimReceiptDetail,
    ProductionIssue, ProductionIssueDetail, FinishedGoods,
    FinishedGoodsProduction, Dispatch, DispatchDetail,
    StockMovement, StockAdjustment, StockAdjustmentDetail,
    Machine, MachineEvent, SparePart, SparePartConsumption,
    StationeryItem, StationeryConsumption, SupplyAdjustment,
)
from datetime import date
from decimal import Decimal

class FabricForm(forms.ModelForm):
    lot_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Optional - creates the fabric's first stock lot. Must be unique.",
    )
    initial_quantity = forms.DecimalField(
        required=False, min_value=0, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        help_text="Starting quantity for the lot above (if given).",
    )

    class Meta:
        model = Fabric
        fields = ['fabric_name', 'fabric_type', 'color', 'gsm',
                 'width', 'supplier', 'style', 'purchase_order', 'buyer',
                 'unit', 'unit_price', 'min_stock', 'max_stock', 'description']
        widgets = {
            'fabric_name': forms.TextInput(attrs={'class': 'form-control'}),
            'fabric_type': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'gsm': forms.NumberInput(attrs={'class': 'form-control'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'style': forms.Select(attrs={'class': 'form-select'}),
            'purchase_order': forms.Select(attrs={'class': 'form-select'}),
            'buyer': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_lot_number(self):
        lot_number = self.cleaned_data.get('lot_number', '').strip()
        if lot_number and FabricRoll.objects.filter(lot_number=lot_number).exists():
            raise forms.ValidationError("A lot with this number already exists.")
        return lot_number

class FabricRollForm(forms.ModelForm):
    class Meta:
        model = FabricRoll
        fields = ['roll_number', 'fabric', 'lot_number', 'length', 'location',
                 'rack_number', 'bin_number', 'received_date', 'expiry_date']
        widgets = {
            'roll_number': forms.TextInput(attrs={'class': 'form-control'}),
            'fabric': forms.Select(attrs={'class': 'form-select'}),
            'lot_number': forms.TextInput(attrs={'class': 'form-control'}),
            'length': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'rack_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bin_number': forms.TextInput(attrs={'class': 'form-control'}),
            'received_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class TrimForm(forms.ModelForm):
    class Meta:
        model = Trim
        fields = ['trim_name', 'trim_type', 'supplier', 'unit',
                 'unit_price', 'reorder_level', 'min_stock', 'max_stock',
                 'color', 'size', 'description']
        widgets = {
            'trim_name': forms.TextInput(attrs={'class': 'form-control'}),
            'trim_type': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'size': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class GoodsReceiptForm(forms.ModelForm):
    class Meta:
        model = GoodsReceipt
        # receipt_number is auto-generated (see GoodsReceipt.receipt_number).
        # No receipt_type/purchase_order/inspection fields anymore - a GR is
        # just "these fabrics were added to stock".
        fields = ['supplier', 'invoice_number', 'invoice_date', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class GoodsReceiptDetailForm(forms.ModelForm):
    class Meta:
        model = GoodsReceiptDetail
        fields = ['fabric', 'quantity', 'unit_price']
        widgets = {
            'fabric': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

class TrimReceiptForm(forms.ModelForm):
    class Meta:
        model = TrimReceipt
        # receipt_number is auto-generated (see TrimReceipt.receipt_number).
        fields = ['supplier', 'invoice_number', 'invoice_date', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TrimReceiptDetailForm(forms.ModelForm):
    class Meta:
        model = TrimReceiptDetail
        fields = ['trim', 'quantity', 'unit_price']
        widgets = {
            'trim': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

class ProductionIssueForm(forms.ModelForm):
    class Meta:
        model = ProductionIssue
        fields = ['issue_number', 'style', 'issue_date', 'department',
                 'production_line', 'notes']
        widgets = {
            'issue_number': forms.TextInput(attrs={'class': 'form-control'}),
            'style': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'production_line': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ProductionIssueDetailForm(forms.ModelForm):
    class Meta:
        model = ProductionIssueDetail
        fields = ['fabric', 'fabric_roll', 'trim', 'quantity_requested',
                 'quantity_issued', 'notes']
        widgets = {
            'fabric': forms.Select(attrs={'class': 'form-select'}),
            'fabric_roll': forms.Select(attrs={'class': 'form-select'}),
            'trim': forms.Select(attrs={'class': 'form-select'}),
            'quantity_requested': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity_issued': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

class FinishedGoodsForm(forms.ModelForm):
    class Meta:
        model = FinishedGoods
        fields = ['sku_code', 'size', 'color', 'unit_price',
                 'warehouse_location', 'rack_location', 'bin_location',
                 'minimum_stock', 'maximum_stock', 'reorder_level', 'description']
        widgets = {
            'sku_code': forms.TextInput(attrs={'class': 'form-control'}),
            'size': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'warehouse_location': forms.TextInput(attrs={'class': 'form-control'}),
            'rack_location': forms.TextInput(attrs={'class': 'form-control'}),
            'bin_location': forms.TextInput(attrs={'class': 'form-control'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'maximum_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class FinishedGoodsStockInForm(forms.Form):
    """
    Adds stock to an existing finished goods item - e.g. a production batch
    just came off the line. Deliberately standalone (not a ModelForm) since
    it doesn't map to a single model: it bumps FinishedGoods.quantity_in_stock
    and quantity_produced, and logs a StockMovement, without needing a style,
    buyer or supplier from another module.
    """
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="How many units to add to stock.",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text="Optional - e.g. batch/reference number.",
    )

class DispatchForm(forms.ModelForm):
    class Meta:
        model = Dispatch
        fields = ['dispatch_number', 'style', 'buyer', 'purchase_order', 'dispatch_date',
                 'total_cartons', 'shipping_line', 'vessel_name', 'vessel_number',
                 'container_number', 'container_size', 'bl_number', 'bl_date',
                 'ex_factory_date', 'shipping_agent', 'notes']
        widgets = {
            'dispatch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'style': forms.Select(attrs={'class': 'form-select'}),
            'buyer': forms.Select(attrs={'class': 'form-select'}),
            'purchase_order': forms.Select(attrs={'class': 'form-select'}),
            'dispatch_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_cartons': forms.NumberInput(attrs={'class': 'form-control'}),
            'shipping_line': forms.TextInput(attrs={'class': 'form-control'}),
            'vessel_name': forms.TextInput(attrs={'class': 'form-control'}),
            'vessel_number': forms.TextInput(attrs={'class': 'form-control'}),
            'container_number': forms.TextInput(attrs={'class': 'form-control'}),
            'container_size': forms.TextInput(attrs={'class': 'form-control'}),
            'bl_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bl_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ex_factory_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'shipping_agent': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DispatchDetailForm(forms.ModelForm):
    class Meta:
        model = DispatchDetail
        fields = ['finished_goods', 'carton_number', 'quantity',
                 'carton_weight', 'carton_dimensions', 'notes']
        widgets = {
            'finished_goods': forms.Select(attrs={'class': 'form-select'}),
            'carton_number': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'carton_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'carton_dimensions': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

class StockAdjustmentForm(forms.ModelForm):
    class Meta:
        model = StockAdjustment
        # adjustment_number is auto-generated (see StockAdjustment.adjustment_number).
        # fabric_roll is intentionally excluded here - lot-wise fabric
        # adjustments go through fabric_stock_adjust/StockAdjustmentDetail
        # instead, so this generic form only ever targets a whole
        # fabric/trim/finished-goods item (no lot granularity).
        fields = ['adjustment_type', 'direction', 'fabric',
                 'trim', 'finished_goods', 'adjustment_date', 'quantity',
                 'reason', 'notes']
        widgets = {
            'adjustment_type': forms.Select(attrs={'class': 'form-select'}),
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'fabric': forms.Select(attrs={'class': 'form-select'}),
            'trim': forms.Select(attrs={'class': 'form-select'}),
            'finished_goods': forms.Select(attrs={'class': 'form-select'}),
            'adjustment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        fabric = cleaned_data.get('fabric')
        trim = cleaned_data.get('trim')
        finished_goods = cleaned_data.get('finished_goods')
        quantity = cleaned_data.get('quantity')
        direction = cleaned_data.get('direction')

        targets = [t for t in [fabric, trim, finished_goods] if t]
        if len(targets) == 0:
            raise forms.ValidationError("Select a fabric, trim, or finished goods item to adjust.")
        if len(targets) > 1:
            raise forms.ValidationError("Select only one of fabric, trim, or finished goods per adjustment.")

        # Stock can never go below 0 - check this up front so the user gets
        # a clear, specific error instead of the adjustment silently failing
        # or (worse) leaving negative stock.
        if direction == 'decrease' and quantity is not None:
            target = targets[0]
            current_stock = target.current_stock if fabric or trim else target.quantity_in_stock
            if quantity > current_stock:
                raise forms.ValidationError(
                    f"Can't decrease stock by {quantity}: only {current_stock} currently in stock."
                )

        return cleaned_data

class RejectStockAdjustmentForm(forms.Form):
    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text="Why this adjustment is being rejected.",
    )

class TrimStockInForm(forms.Form):
    """
    Adds stock to an existing trim item. Deliberately simple (no lot
    tracking - trims aren't batch/dye-lot sensitive the way fabric is),
    mirrors FinishedGoodsStockInForm.
    """
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="How many units to add to stock.",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text="Optional - e.g. supplier/invoice reference.",
    )

class FabricStockInForm(forms.Form):
    """
    Adds a brand-new lot to an existing fabric. Every stock-in for Fabric is
    a new, uniquely-numbered lot (unlike Trim/FinishedGoods stock-in, which
    just bumps a plain quantity) so the item can be traced/issued lot-wise.
    """
    lot_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Must be unique across all fabric lots.",
    )
    quantity = forms.DecimalField(
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    location = forms.CharField(
        initial='Main Warehouse',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    received_date = forms.DateField(
        initial=date.today,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
    )

    def clean_lot_number(self):
        lot_number = self.cleaned_data['lot_number'].strip()
        if FabricRoll.objects.filter(lot_number=lot_number).exists():
            raise forms.ValidationError("A lot with this number already exists.")
        return lot_number

class FabricLotAdjustForm(forms.Form):
    """
    Header for a lot-wise Fabric Adjust/Issue action - the per-lot quantity
    rows are parsed from the POST data directly in the view, the same way
    add_goods_receipt already parses its multi-row fabric_ids[]/quantities[].
    """
    adjustment_type = forms.ChoiceField(choices=StockAdjustment.ADJUSTMENT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}))
    direction = forms.ChoiceField(choices=StockAdjustment.DIRECTION_CHOICES, initial='decrease',
        widget=forms.Select(attrs={'class': 'form-select'}))
    purchase_order = forms.ModelChoiceField(
        queryset=None, required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Optional - which PO this fabric is being issued against.",
    )
    adjustment_date = forms.DateField(
        initial=date.today,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    reason = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.accounts.models import PurchaseOrder
        self.fields['purchase_order'].queryset = PurchaseOrder.objects.all()

# ------------------------------------------------------------------ machines

class MachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = ['machine_code', 'machine_name', 'machine_type', 'brand', 'model_number',
                 'serial_number', 'supplier', 'department', 'line_number', 'location',
                 'purchase_date', 'purchase_cost', 'warranty_expiry', 'description']
        widgets = {
            'machine_code': forms.TextInput(attrs={'class': 'form-control'}),
            'machine_name': forms.TextInput(attrs={'class': 'form-control'}),
            'machine_type': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'line_number': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'warranty_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MachineEventForm(forms.ModelForm):
    class Meta:
        model = MachineEvent
        fields = ['event_type', 'event_date', 'description', 'cost', 'counterparty']
        widgets = {
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'event_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'counterparty': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buyer / vendor / technician'}),
        }

class RejectMachineEventForm(forms.Form):
    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text="Why this request is being rejected.",
    )

# --------------------------------------------------------------- spare parts

class SparePartForm(forms.ModelForm):
    class Meta:
        model = SparePart
        fields = ['part_name', 'category', 'compatible_machine_type', 'supplier',
                 'unit', 'unit_price', 'min_stock', 'max_stock', 'description']
        widgets = {
            'part_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'compatible_machine_type': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SparePartStockInForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="How many units to add to stock.",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text="Optional - e.g. supplier/invoice reference.",
    )

class SparePartConsumptionForm(forms.Form):
    department = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    machine = forms.ModelChoiceField(
        queryset=None, required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Optional - which machine this part was used to repair.",
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    consumption_date = forms.DateField(
        initial=date.today,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.hr.models import Department
        self.fields['department'].queryset = Department.objects.all()
        self.fields['machine'].queryset = Machine.objects.exclude(status__in=['sold', 'scrapped'])

# ---------------------------------------------------------------- stationery

class StationeryItemForm(forms.ModelForm):
    class Meta:
        model = StationeryItem
        fields = ['item_name', 'category', 'unit', 'unit_price', 'min_stock', 'max_stock', 'description']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class StationeryStockInForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="How many units to add to stock.",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text="Optional - e.g. supplier/invoice reference.",
    )

class StationeryConsumptionForm(forms.Form):
    department = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    consumption_date = forms.DateField(
        initial=date.today,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.hr.models import Department
        self.fields['department'].queryset = Department.objects.all()

# ------------------------------------------------------------- supply adjustment

class SupplyAdjustmentForm(forms.ModelForm):
    class Meta:
        model = SupplyAdjustment
        fields = ['adjustment_type', 'direction', 'spare_part', 'stationery_item',
                 'adjustment_date', 'quantity', 'reason', 'notes']
        widgets = {
            'adjustment_type': forms.Select(attrs={'class': 'form-select'}),
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'spare_part': forms.Select(attrs={'class': 'form-select'}),
            'stationery_item': forms.Select(attrs={'class': 'form-select'}),
            'adjustment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        spare_part = cleaned_data.get('spare_part')
        stationery_item = cleaned_data.get('stationery_item')
        quantity = cleaned_data.get('quantity')
        direction = cleaned_data.get('direction')

        targets = [t for t in [spare_part, stationery_item] if t]
        if len(targets) == 0:
            raise forms.ValidationError("Select a spare part or a stationery item to adjust.")
        if len(targets) > 1:
            raise forms.ValidationError("Select only one of spare part or stationery item per adjustment.")

        if direction == 'decrease' and quantity is not None:
            current_stock = targets[0].current_stock
            if quantity > current_stock:
                raise forms.ValidationError(
                    f"Can't decrease stock by {quantity}: only {current_stock} currently in stock."
                )

        return cleaned_data

class RejectSupplyAdjustmentForm(forms.Form):
    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text="Why this adjustment is being rejected.",
    )