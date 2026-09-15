from django import forms
from .models import (
    Fabric, FabricRoll, Trim, GoodsReceipt, GoodsReceiptDetail,
    TrimReceipt, TrimReceiptDetail,
    ProductionIssue, ProductionIssueDetail, FinishedGoods,
    FinishedGoodsProduction, Dispatch, DispatchDetail,
    StockMovement, StockAdjustment
)
from datetime import date

class FabricForm(forms.ModelForm):
    class Meta:
        model = Fabric
        fields = ['fabric_name', 'fabric_type', 'color', 'gsm',
                 'width', 'supplier', 'unit', 'unit_price', 'reorder_level',
                 'min_stock', 'max_stock', 'description']
        widgets = {
            'fabric_name': forms.TextInput(attrs={'class': 'form-control'}),
            'fabric_type': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'gsm': forms.NumberInput(attrs={'class': 'form-control'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

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
        fields = ['dispatch_number', 'style', 'buyer', 'dispatch_date',
                 'total_cartons', 'shipping_line', 'vessel_name', 'vessel_number',
                 'container_number', 'container_size', 'bl_number', 'bl_date',
                 'ex_factory_date', 'shipping_agent', 'notes']
        widgets = {
            'dispatch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'style': forms.Select(attrs={'class': 'form-select'}),
            'buyer': forms.Select(attrs={'class': 'form-select'}),
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
        fields = ['adjustment_type', 'direction', 'fabric', 'fabric_roll',
                 'trim', 'finished_goods', 'adjustment_date', 'quantity',
                 'reason', 'notes']
        widgets = {
            'adjustment_type': forms.Select(attrs={'class': 'form-select'}),
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'fabric': forms.Select(attrs={'class': 'form-select'}),
            'fabric_roll': forms.Select(attrs={'class': 'form-select'}),
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