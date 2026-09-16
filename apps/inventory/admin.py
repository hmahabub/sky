from django.contrib import admin

from .models import (
    Fabric, FabricRoll, Trim, GoodsReceipt, GoodsReceiptDetail,
    TrimReceipt, TrimReceiptDetail,
    ProductionIssue, ProductionIssueDetail, FinishedGoods,
    FinishedGoodsProduction, Dispatch, DispatchDetail, StockMovement,
    StockAdjustment, StockAdjustmentDetail,
)

admin.site.register(Fabric)
admin.site.register(FabricRoll)
admin.site.register(Trim)
admin.site.register(GoodsReceipt)
admin.site.register(GoodsReceiptDetail)
admin.site.register(TrimReceipt)
admin.site.register(TrimReceiptDetail)
admin.site.register(ProductionIssue)
admin.site.register(ProductionIssueDetail)
admin.site.register(FinishedGoods)
admin.site.register(FinishedGoodsProduction)
admin.site.register(Dispatch)
admin.site.register(DispatchDetail)
admin.site.register(StockMovement)

class StockAdjustmentDetailInline(admin.TabularInline):
    model = StockAdjustmentDetail
    extra = 0

@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('adjustment_number', 'adjustment_type', 'direction', 'status', 'adjustment_date', 'created_by')
    list_filter = ('status', 'adjustment_type', 'direction')
    inlines = [StockAdjustmentDetailInline]
