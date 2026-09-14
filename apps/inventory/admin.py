from django.contrib import admin

from .models import (
    Fabric, FabricRoll, Trim, GoodsReceipt, GoodsReceiptDetail,
    TrimReceipt, TrimReceiptDetail,
    ProductionIssue, ProductionIssueDetail, FinishedGoods,
    FinishedGoodsProduction, Dispatch, DispatchDetail, StockMovement,
    StockAdjustment,
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
admin.site.register(StockAdjustment)
