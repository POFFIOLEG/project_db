from rest_framework import serializers

from .models import MasterDataSyncJob


class MasterDataSyncJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterDataSyncJob
        fields = [
            "id",
            "payload_type",
            "direction",
            "payload",
            "result_summary",
            "status",
            "requested_by",
            "started_at",
            "finished_at",
            "message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "result_summary",
            "status",
            "started_at",
            "finished_at",
            "message",
            "created_at",
            "updated_at",
        ]


