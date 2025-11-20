from django.contrib import admin

from .models import MasterDataSyncJob


@admin.register(MasterDataSyncJob)
class MasterDataSyncJobAdmin(admin.ModelAdmin):
    list_display = ("payload_type", "direction", "status", "created_at", "finished_at")
    list_filter = ("payload_type", "direction", "status")
    search_fields = ("id", "message")
    readonly_fields = ("created_at", "updated_at", "started_at", "finished_at", "result_summary")


