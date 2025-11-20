from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, List, TypedDict

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from inventory.models import Product, StockArea
from pricing.models import PriceRestriction
from references.models import (
    Contract,
    ContractItem,
    Country,
    Manufacturer,
    StorageLocation,
    Supplier,
    SupplierContact,
    Truck,
)
from staff.models import AccessRole, Department, Employee, Position

from .models import MasterDataSyncJob

User = get_user_model()


class SyncSummary(TypedDict, total=False):
    countries: int
    manufacturers: int
    products: int
    suppliers: int
    supplier_contacts: int
    storage_locations: int
    stock_areas: int
    trucks: int
    contracts: int
    contract_items: int
    positions: int
    departments: int
    roles: int
    employees: int


class MasterDataSyncService:
    """
    Applies master-data payloads from HQ to local reference tables.
    Expected payload structure:
    {
        "countries": [{"code": "...", "name": "..."}],
        "manufacturers": [{"name": "...", "country_code": "...", "company_code": "..."}],
        "products": [{
            "sku": "...",
            "name": "...",
            "manufacturer_code": "...",
            "country_code": "...",
            "barcode": "...",
            "dimensions": "",
            "unit": "pcs",
            "shelf_life_days": 120,
            "category": "",
            "extra_info": "",
            "price_restriction": {"max_markup_percent": 15, "max_daily_change_percent": 5}
        }],
        ...
    }
    """

    def __init__(self, job: MasterDataSyncJob):
        self.job = job

    def run(self) -> MasterDataSyncJob:
        self.job.status = MasterDataSyncJob.STATUS_PROCESSING
        self.job.started_at = timezone.now()
        self.job.message = ""
        self.job.save(update_fields=["status", "started_at", "message", "updated_at"])

        try:
            summary = self._apply_payload(self.job.payload or {})
        except Exception as exc:  # noqa: BLE001
            self.job.status = MasterDataSyncJob.STATUS_FAILED
            self.job.message = str(exc)
            self.job.finished_at = timezone.now()
            self.job.save(update_fields=["status", "message", "finished_at", "updated_at"])
            raise

        self.job.status = MasterDataSyncJob.STATUS_SUCCESS
        self.job.result_summary = summary
        self.job.finished_at = timezone.now()
        self.job.save(update_fields=["status", "result_summary", "finished_at", "updated_at"])
        return self.job

    @transaction.atomic
    def _apply_payload(self, payload: Dict) -> SyncSummary:
        summary: SyncSummary = {}

        summary["countries"] = self._sync_countries(payload.get("countries", []))
        summary["manufacturers"] = self._sync_manufacturers(payload.get("manufacturers", []))
        summary["products"] = self._sync_products(payload.get("products", []))

        summary["suppliers"] = self._sync_suppliers(payload.get("suppliers", []))
        summary["supplier_contacts"] = self._sync_supplier_contacts(payload.get("supplier_contacts", []))

        summary["storage_locations"] = self._sync_storage_locations(payload.get("storage_locations", []))
        summary["stock_areas"] = self._sync_stock_areas(payload.get("stock_areas", []))
        summary["trucks"] = self._sync_trucks(payload.get("trucks", []))

        summary["contracts"] = self._sync_contracts(payload.get("contracts", []))
        summary["contract_items"] = self._sync_contract_items(payload.get("contract_items", []))

        summary["departments"] = self._sync_departments(payload.get("departments", []))
        summary["positions"] = self._sync_positions(payload.get("positions", []))
        summary["roles"] = self._sync_roles(payload.get("roles", []))
        summary["employees"] = self._sync_employees(payload.get("employees", []))

        return summary

    # --- References -----------------------------------------------------

    def _sync_countries(self, entries: Iterable[Dict]) -> int:
        count = 0
        for entry in entries:
            Country.objects.update_or_create(
                code=entry["code"],
                defaults={"name": entry.get("name", entry["code"])},
            )
            count += 1
        return count

    def _sync_manufacturers(self, entries: Iterable[Dict]) -> int:
        count = 0
        for entry in entries:
            country = Country.objects.get(code=entry["country_code"])
            Manufacturer.objects.update_or_create(
                name=entry["name"],
                defaults={
                    "country": country,
                    "company_code": entry.get("company_code", ""),
                },
            )
            count += 1
        return count

    def _sync_products(self, entries: Iterable[Dict]) -> int:
        count = 0
        for entry in entries:
            manufacturer = Manufacturer.objects.get(name=entry["manufacturer_name"])
            country = Country.objects.get(code=entry["country_code"])
            product, _ = Product.objects.update_or_create(
                sku=entry["sku"],
                defaults={
                    "name": entry["name"],
                    "manufacturer": manufacturer,
                    "manufacturer_code": entry.get("manufacturer_code", ""),
                    "country": country,
                    "dimensions": entry.get("dimensions", ""),
                    "unit": entry.get("unit", Product.UNIT_CHOICES[0][0]),
                    "shelf_life_days": entry.get("shelf_life_days", 0),
                    "barcode": entry["barcode"],
                    "category": entry.get("category", ""),
                    "extra_info": entry.get("extra_info", ""),
                },
            )
            restriction = entry.get("price_restriction")
            if restriction:
                PriceRestriction.objects.update_or_create(
                    product=product,
                    defaults={
                        "max_markup_percent": restriction.get("max_markup_percent", 1000),
                        "max_daily_change_percent": restriction.get("max_daily_change_percent", 90),
                        "allow_auto_markdown": restriction.get("allow_auto_markdown", True),
                    },
                )
            count += 1
        return count

    def _sync_suppliers(self, entries: Iterable[Dict]) -> int:
        count = 0
        for entry in entries:
            country = Country.objects.get(code=entry["country_code"])
            Supplier.objects.update_or_create(
                tax_number=entry["tax_number"],
                defaults={
                    "name": entry["name"],
                    "country": country,
                    "address": entry.get("address", ""),
                    "email": entry.get("email", ""),
                    "phone": entry.get("phone", ""),
                },
            )
            count += 1
        return count

    def _sync_supplier_contacts(self, entries: Iterable[Dict]) -> int:
        count = 0
        for entry in entries:
            supplier = Supplier.objects.get(tax_number=entry["supplier_tax_number"])
            SupplierContact.objects.update_or_create(
                supplier=supplier,
                name=entry["name"],
                defaults={
                    "position": entry.get("position", ""),
                    "phone": entry.get("phone", ""),
                    "email": entry.get("email", ""),
                },
            )
            count += 1
        return count

    def _sync_storage_locations(self, entries: Iterable[Dict]) -> int:
        count = 0
        for entry in entries:
            StorageLocation.objects.update_or_create(
                code=entry["code"],
                defaults={
                    "name": entry["name"],
                    "location_type": entry.get("location_type", StorageLocation.WAREHOUSE),
                    "address": entry.get("address", ""),
                    "temperature_min": entry.get("temperature_min"),
                    "temperature_max": entry.get("temperature_max"),
                    "capacity_units": entry.get("capacity_units", 0),
                },
            )
            count += 1
        return count

    def _sync_stock_areas(self, entries: Iterable[Dict]) -> int:
        count = 0
        for entry in entries:
            parent = StorageLocation.objects.get(code=entry["storage_code"])
            StockArea.objects.update_or_create(
                code=entry["code"],
                defaults={
                    "name": entry["name"],
                    "area_type": entry.get("area_type", StockArea.WAREHOUSE),
                    "parent_location": parent,
                    "max_capacity": entry.get("max_capacity", 0),
                    "temperature_min": entry.get("temperature_min"),
                    "temperature_max": entry.get("temperature_max"),
                },
            )
            count += 1
        return count

    def _sync_trucks(self, entries: Iterable[Dict]) -> int:
        count = 0
        for entry in entries:
            Truck.objects.update_or_create(
                number=entry["number"],
                defaults={
                    "capacity_kg": entry.get("capacity_kg", 0),
                    "driver_name": entry.get("driver_name", ""),
                    "active": entry.get("active", True),
                },
            )
            count += 1
        return count

    def _sync_contracts(self, entries: Iterable[Dict]) -> int:
        count = 0
        for entry in entries:
            supplier = Supplier.objects.get(tax_number=entry["supplier_tax_number"])
            location = None
            if entry.get("storage_code"):
                location = StorageLocation.objects.get(code=entry["storage_code"])
            truck = None
            if entry.get("truck_number"):
                truck, _ = Truck.objects.get_or_create(number=entry["truck_number"], defaults={"capacity_kg": 0})
            Contract.objects.update_or_create(
                contract_number=entry["contract_number"],
                defaults={
                    "supplier": supplier,
                    "signed_at": self._as_date(entry.get("signed_at")) or date.today(),
                    "valid_until": self._as_date(entry.get("valid_until")),
                    "direct_delivery": entry.get("direct_delivery", False),
                    "storage_location": location,
                    "truck": truck,
                },
            )
            count += 1
        return count

    def _sync_contract_items(self, entries: Iterable[Dict]) -> int:
        count = 0
        for entry in entries:
            contract = Contract.objects.get(contract_number=entry["contract_number"])
            product = Product.objects.get(sku=entry["product_sku"])
            ContractItem.objects.update_or_create(
                contract=contract,
                product=product,
                defaults={
                    "expected_quantity": entry.get("expected_quantity", 0),
                    "unit_price": entry.get("unit_price", 0),
                },
            )
            count += 1
        return count

    # --- Staff ----------------------------------------------------------

    def _sync_departments(self, entries: Iterable[Dict]) -> int:
        count = 0
        for entry in entries:
            Department.objects.update_or_create(
                name=entry["name"],
                defaults={"description": entry.get("description", "")},
            )
            count += 1
        return count

    def _sync_positions(self, entries: Iterable[Dict]) -> int:
        count = 0
        for entry in entries:
            Position.objects.update_or_create(
                name=entry["name"],
                defaults={
                    "monthly_hours": entry.get("monthly_hours", 160),
                    "hourly_rate": entry.get("hourly_rate", 0),
                    "responsibilities": entry.get("responsibilities", ""),
                },
            )
            count += 1
        return count

    def _sync_roles(self, entries: Iterable[Dict]) -> int:
        count = 0
        for entry in entries:
            AccessRole.objects.update_or_create(
                code=entry["code"],
                defaults={
                    "name": entry.get("name", entry["code"]),
                    "description": entry.get("description", ""),
                },
            )
            count += 1
        return count

    def _sync_employees(self, entries: Iterable[Dict]) -> int:
        count = 0
        for entry in entries:
            username = entry["username"]
            user_defaults = {
                "email": entry.get("work_email") or entry.get("personal_email") or "",
                "first_name": entry.get("full_name", "").split(" ")[0] if entry.get("full_name") else "",
            }
            user, created = User.objects.get_or_create(username=username, defaults=user_defaults)
            if entry.get("password"):
                user.set_password(entry["password"])
                user.save(update_fields=["password"])
            elif created:
                user.set_password(User.objects.make_random_password())
                user.save()

            department = None
            if entry.get("department_name"):
                department, _ = Department.objects.get_or_create(name=entry["department_name"])

            position = None
            if entry.get("position_name"):
                position, _ = Position.objects.get_or_create(name=entry["position_name"])

            role = None
            if entry.get("role_code"):
                role, _ = AccessRole.objects.get_or_create(code=entry["role_code"], defaults={"name": entry["role_code"]})

            Employee.objects.update_or_create(
                user=user,
                defaults={
                    "full_name": entry.get("full_name", username),
                    "passport_series": entry.get("passport_series", ""),
                    "passport_number": entry.get("passport_number", ""),
                    "passport_address": entry.get("passport_address", ""),
                    "foreign_passport": entry.get("foreign_passport", ""),
                    "birth_date": self._as_date(entry.get("birth_date")),
                    "department": department,
                    "position": position,
                    "work_phone": entry.get("work_phone", ""),
                    "personal_phone": entry.get("personal_phone", ""),
                    "work_email": entry.get("work_email", ""),
                    "personal_email": entry.get("personal_email", ""),
                    "role": role,
                    "status": entry.get("status", Employee.ACTIVE),
                    "hired_at": self._as_date(entry.get("hired_at")),
                    "fired_at": self._as_date(entry.get("fired_at")),
                },
            )
            count += 1
        return count

    def _as_date(self, value):
        if not value:
            return None
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except ValueError as exc:  # noqa: BLE001
            raise ValueError(f"Cannot parse date '{value}'") from exc


class MasterDataExportService:
    """
    Aggregates local master data for HQ.
    """

    def export(self, dataset: str = "full") -> Dict[str, List[Dict]]:
        exporters = {
            "countries": self._export_countries,
            "manufacturers": self._export_manufacturers,
            "products": self._export_products,
            "suppliers": self._export_suppliers,
            "supplier_contacts": self._export_supplier_contacts,
            "storage_locations": self._export_storage_locations,
            "stock_areas": self._export_stock_areas,
            "trucks": self._export_trucks,
            "contracts": self._export_contracts,
            "contract_items": self._export_contract_items,
            "departments": self._export_departments,
            "positions": self._export_positions,
            "roles": self._export_roles,
            "employees": self._export_employees,
        }

        if dataset == "full":
            return {key: exporter() for key, exporter in exporters.items()}
        if dataset not in exporters:
            raise ValueError(f"Unknown dataset '{dataset}'")
        return {dataset: exporters[dataset]()}

    def _export_countries(self) -> List[Dict]:
        return list(Country.objects.values("code", "name"))

    def _export_manufacturers(self) -> List[Dict]:
        return [
            {
                "name": manufacturer.name,
                "country_code": manufacturer.country.code,
                "company_code": manufacturer.company_code,
            }
            for manufacturer in Manufacturer.objects.select_related("country")
        ]

    def _export_products(self) -> List[Dict]:
        products = Product.objects.select_related("manufacturer", "country")
        restrictions = PriceRestriction.objects.in_bulk(field_name="product_id")
        result: List[Dict] = []
        for product in products:
            entry = {
                "sku": product.sku,
                "name": product.name,
                "manufacturer_name": product.manufacturer.name,
                "manufacturer_code": product.manufacturer_code,
                "country_code": product.country.code,
                "dimensions": product.dimensions,
                "unit": product.unit,
                "shelf_life_days": product.shelf_life_days,
                "barcode": product.barcode,
                "category": product.category,
                "extra_info": product.extra_info,
            }
            restriction = restrictions.get(product.id)
            if restriction:
                entry["price_restriction"] = {
                    "max_markup_percent": str(restriction.max_markup_percent),
                    "max_daily_change_percent": str(restriction.max_daily_change_percent),
                    "allow_auto_markdown": restriction.allow_auto_markdown,
                }
            result.append(entry)
        return result

    def _export_suppliers(self) -> List[Dict]:
        return [
            {
                "tax_number": supplier.tax_number,
                "name": supplier.name,
                "country_code": supplier.country.code,
                "address": supplier.address,
                "email": supplier.email,
                "phone": supplier.phone,
            }
            for supplier in Supplier.objects.select_related("country")
        ]

    def _export_supplier_contacts(self) -> List[Dict]:
        return [
            {
                "supplier_tax_number": contact.supplier.tax_number,
                "name": contact.name,
                "position": contact.position,
                "phone": contact.phone,
                "email": contact.email,
            }
            for contact in SupplierContact.objects.select_related("supplier")
        ]

    def _export_storage_locations(self) -> List[Dict]:
        return list(
            StorageLocation.objects.values(
                "code",
                "name",
                "location_type",
                "address",
                "temperature_min",
                "temperature_max",
                "capacity_units",
            )
        )

    def _export_stock_areas(self) -> List[Dict]:
        return [
            {
                "code": area.code,
                "name": area.name,
                "area_type": area.area_type,
                "storage_code": area.parent_location.code,
                "max_capacity": str(area.max_capacity),
                "temperature_min": area.temperature_min,
                "temperature_max": area.temperature_max,
            }
            for area in StockArea.objects.select_related("parent_location")
        ]

    def _export_trucks(self) -> List[Dict]:
        return list(Truck.objects.values("number", "capacity_kg", "driver_name", "active"))

    def _export_contracts(self) -> List[Dict]:
        return [
            {
                "contract_number": contract.contract_number,
                "supplier_tax_number": contract.supplier.tax_number,
                "signed_at": contract.signed_at,
                "valid_until": contract.valid_until,
                "direct_delivery": contract.direct_delivery,
                "storage_code": contract.storage_location.code if contract.storage_location else None,
                "truck_number": contract.truck.number if contract.truck else None,
            }
            for contract in Contract.objects.select_related("supplier", "storage_location", "truck")
        ]

    def _export_contract_items(self) -> List[Dict]:
        return [
            {
                "contract_number": item.contract.contract_number,
                "product_sku": item.product.sku,
                "expected_quantity": str(item.expected_quantity),
                "unit_price": str(item.unit_price),
            }
            for item in ContractItem.objects.select_related("contract", "product")
        ]

    def _export_departments(self) -> List[Dict]:
        return list(Department.objects.values("name", "description"))

    def _export_positions(self) -> List[Dict]:
        return list(Position.objects.values("name", "monthly_hours", "hourly_rate", "responsibilities"))

    def _export_roles(self) -> List[Dict]:
        return list(AccessRole.objects.values("code", "name", "description"))

    def _export_employees(self) -> List[Dict]:
        employees = Employee.objects.select_related("user", "department", "position", "role")
        result: List[Dict] = []
        for employee in employees:
            result.append(
                {
                    "username": employee.user.username,
                    "full_name": employee.full_name,
                    "department_name": employee.department.name if employee.department else None,
                    "position_name": employee.position.name if employee.position else None,
                    "role_code": employee.role.code if employee.role else None,
                    "passport_series": employee.passport_series,
                    "passport_number": employee.passport_number,
                    "passport_address": employee.passport_address,
                    "foreign_passport": employee.foreign_passport,
                    "birth_date": employee.birth_date,
                    "work_phone": employee.work_phone,
                    "personal_phone": employee.personal_phone,
                    "work_email": employee.work_email,
                    "personal_email": employee.personal_email,
                    "status": employee.status,
                    "hired_at": employee.hired_at,
                    "fired_at": employee.fired_at,
                }
            )
        return result


