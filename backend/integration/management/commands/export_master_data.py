import json
from pathlib import Path

from django.core.management import BaseCommand

from integration.models import MasterDataSyncJob
from integration.services import MasterDataExportService


class Command(BaseCommand):
    help = "Export current master data snapshot to a JSON file for HQ."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset",
            default="full",
            help="Dataset alias (full, products, suppliers, etc.).",
        )
        parser.add_argument(
            "--output",
            default="master_data_export.json",
            help="Target JSON file path.",
        )

    def handle(self, *args, **options):
        dataset = options["dataset"]
        output_path = Path(options["output"]).expanduser().resolve()

        self.stdout.write(f"Building export for dataset '{dataset}'")
        payload = MasterDataExportService().export(dataset)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2, default=str)

        MasterDataSyncJob.objects.create(
            payload_type=dataset if dataset != "full" else MasterDataSyncJob.TYPE_FULL,
            direction=MasterDataSyncJob.DIR_OUTBOUND,
            payload=payload,
            status=MasterDataSyncJob.STATUS_SUCCESS,
            result_summary={key: len(value) for key, value in payload.items()},
            message=f"Exported to {output_path}",
        )

        self.stdout.write(self.style.SUCCESS(f"Master data exported to {output_path}"))


