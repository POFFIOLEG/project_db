from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MasterDataSyncJob
from .serializers import MasterDataSyncJobSerializer
from .services import MasterDataExportService, MasterDataSyncService


class MasterDataSyncJobViewSet(viewsets.ModelViewSet):
    queryset = MasterDataSyncJob.objects.all()
    serializer_class = MasterDataSyncJobSerializer
    filterset_fields = ["payload_type", "direction", "status"]

    def perform_create(self, serializer):
        job = serializer.save()
        MasterDataSyncService(job).run()

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        job = self.get_object()
        MasterDataSyncService(job).run()
        serializer = self.get_serializer(job)
        return Response(serializer.data)


class MasterDataExportView(APIView):
    """
    Returns current master data snapshot for HQ.
    """

    def get(self, request):
        dataset = request.query_params.get("dataset", "full")
        service = MasterDataExportService()
        try:
            payload = service.export(dataset)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        job = MasterDataSyncJob.objects.create(
            payload_type=dataset if dataset != "full" else MasterDataSyncJob.TYPE_FULL,
            direction=MasterDataSyncJob.DIR_OUTBOUND,
            payload=payload,
            status=MasterDataSyncJob.STATUS_SUCCESS,
            result_summary={key: len(value) for key, value in payload.items()},
        )
        serializer = MasterDataSyncJobSerializer(job)
        response_data = {"payload": payload, "job": serializer.data}
        return Response(response_data)


