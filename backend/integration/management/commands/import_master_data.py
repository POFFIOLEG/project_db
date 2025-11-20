import json
from pathlib import Path

from django.core.management import BaseCommand, CommandError

from integration.models import MasterDataSyncJob
from integration.services import MasterDataSyncService


class Command(BaseCommand):
    help = "Load master data payload received from HQ (JSON file) and apply it to local references."

    def add_arguments(self, parser):
        parser.add_argument("payload", type=str, help="Path to JSON file provided by HQ.")
        parser.add_argument(
            "--payload-type",
            default=MasterDataSyncJob.TYPE_FULL,
            choices=[choice[0] for choice in MasterDataSyncJob.TYPE_CHOICES],
            help="Type of payload for reporting purposes.",
        )

    def handle(self, *args, **options):
        file_path = Path(options["payload"]).expanduser().resolve()
        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        self.stdout.write(f"Reading payload from {file_path}")
        with file_path.open("r", encoding="utf-8") as fp:
            payload = json.load(fp)

        job = MasterDataSyncJob.objects.create(
            payload_type=options["payload_type"],
            direction=MasterDataSyncJob.DIR_INBOUND,
            payload=payload,
        )

        self.stdout.write("Applying payload...")
        MasterDataSyncService(job).run()
        self.stdout.write(self.style.SUCCESS("Master data imported successfully."))
        self.stdout.write(json.dumps(job.result_summary, ensure_ascii=False, indent=2))


