"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from attendance.views import (
    AttendanceReportLineViewSet,
    AttendanceReportViewSet,
    EmployeeScheduleViewSet,
    LeaveRequestViewSet,
    ScheduleTemplateViewSet,
    WorkSessionViewSet,
)
from inventory.views import (
    InventoryLineViewSet,
    InventorySessionViewSet,
    ProductBatchViewSet,
    ProductViewSet,
    ReceivingDiscrepancyViewSet,
    ReceivingItemViewSet,
    ReceivingOrderViewSet,
    ShelfViewSet,
    StockAreaViewSet,
    StockItemViewSet,
    StockOperationViewSet,
    StockPlacementViewSet,
    WriteOffActViewSet,
)
from integration.views import MasterDataExportView, MasterDataSyncJobViewSet
from pricing.views import (
    CouponViewSet,
    PriceCategoryLimitViewSet,
    PriceCommandItemViewSet,
    PriceCommandViewSet,
    PriceListViewSet,
    PriceRestrictionViewSet,
    StopListEntryViewSet,
)
from references.views import (
    ContractItemViewSet,
    ContractViewSet,
    CountryViewSet,
    ManufacturerViewSet,
    StorageLocationViewSet,
    SupplierContactViewSet,
    SupplierViewSet,
    TruckViewSet,
)
from staff.views import AccessRoleViewSet, DepartmentViewSet, EmployeeViewSet, PositionViewSet

router = DefaultRouter()

# references
router.register('countries', CountryViewSet)
router.register('manufacturers', ManufacturerViewSet)
router.register('suppliers', SupplierViewSet)
router.register('supplier-contacts', SupplierContactViewSet)
router.register('storage-locations', StorageLocationViewSet)
router.register('trucks', TruckViewSet)
router.register('contracts', ContractViewSet)
router.register('contract-items', ContractItemViewSet)

# staff
router.register('departments', DepartmentViewSet)
router.register('positions', PositionViewSet)
router.register('access-roles', AccessRoleViewSet)
router.register('employees', EmployeeViewSet)

# inventory
router.register('products', ProductViewSet)
router.register('stock-areas', StockAreaViewSet)
router.register('shelves', ShelfViewSet)
router.register('product-batches', ProductBatchViewSet)
router.register('stock-items', StockItemViewSet)
router.register('stock-operations', StockOperationViewSet)
router.register('write-off-acts', WriteOffActViewSet)
router.register('inventory-sessions', InventorySessionViewSet)
router.register('inventory-lines', InventoryLineViewSet)
router.register('receiving-orders', ReceivingOrderViewSet)
router.register('receiving-items', ReceivingItemViewSet)
router.register('receiving-discrepancies', ReceivingDiscrepancyViewSet)
router.register('stock-placements', StockPlacementViewSet)

# pricing
router.register('price-restrictions', PriceRestrictionViewSet)
router.register('price-lists', PriceListViewSet)
router.register('coupons', CouponViewSet)
router.register('price-commands', PriceCommandViewSet)
router.register('price-command-items', PriceCommandItemViewSet)
router.register('price-category-limits', PriceCategoryLimitViewSet)
router.register('stop-list', StopListEntryViewSet)

# integration / HQ data exchange
router.register('hq-sync-jobs', MasterDataSyncJobViewSet)

# attendance
router.register('schedule-templates', ScheduleTemplateViewSet)
router.register('work-sessions', WorkSessionViewSet)
router.register('attendance-reports', AttendanceReportViewSet)
router.register('attendance-report-lines', AttendanceReportLineViewSet)
router.register('leave-requests', LeaveRequestViewSet)
router.register('employee-schedules', EmployeeScheduleViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/hq/export/', MasterDataExportView.as_view(), name='hq-export'),
]
