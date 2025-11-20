from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class MasterDataSyncJob(TimestampedModel):
    TYPE_FULL = "full"
    TYPE_REFERENCES = "references"
    TYPE_PRODUCTS = "products"
    TYPE_STAFF = "staff"
    TYPE_CONTRACTS = "contracts"
    TYPE_SUPPLIERS = "suppliers"
    TYPE_STORAGE = "storage"
    TYPE_TRANSPORT = "transport"

    TYPE_CHOICES = [
        (TYPE_FULL, "Полный пакет"),
        (TYPE_REFERENCES, "Базовые справочники"),
        (TYPE_PRODUCTS, "Товары"),
        (TYPE_STAFF, "Сотрудники"),
        (TYPE_CONTRACTS, "Договоры"),
        (TYPE_SUPPLIERS, "Поставщики"),
        (TYPE_STORAGE, "Места хранения"),
        (TYPE_TRANSPORT, "Транспорт"),
    ]

    DIR_INBOUND = "inbound"
    DIR_OUTBOUND = "outbound"
    DIRECTION_CHOICES = [
        (DIR_INBOUND, "Входящий пакет"),
        (DIR_OUTBOUND, "Исходящий пакет"),
    ]

    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Ожидает обработки"),
        (STATUS_PROCESSING, "В работе"),
        (STATUS_SUCCESS, "Успешно"),
        (STATUS_FAILED, "Ошибка"),
    ]

    payload_type = models.CharField(max_length=32, choices=TYPE_CHOICES, default=TYPE_FULL)
    direction = models.CharField(max_length=16, choices=DIRECTION_CHOICES, default=DIR_INBOUND)
    payload = models.JSONField(default=dict, blank=True)
    result_summary = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    requested_by = models.ForeignKey(
        "staff.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_sync_jobs",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Обмен с ГК"
        verbose_name_plural = "Обмен с ГК"

    def __str__(self) -> str:
        return f"{self.get_direction_display()} / {self.get_payload_type_display()} / {self.get_status_display()}"


