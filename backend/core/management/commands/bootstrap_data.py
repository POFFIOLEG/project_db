from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, CommandError, call_command

from references.models import Country


class Command(BaseCommand):
    help = (
        "Apply database migrations and load the default seed data. "
        "Skips loading if data already present unless --force is provided."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture",
            default="seed.json",
            help="Path to the fixture file relative to BASE_DIR (default: seed.json).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Load seed data even if existing data is detected.",
        )

    def handle(self, *args, **options):
        fixture_option = options["fixture"]
        fixture_path = Path(fixture_option)
        if not fixture_path.is_absolute():
            fixture_path = Path(settings.BASE_DIR) / fixture_path
        fixture_path = fixture_path.resolve()

        self.stdout.write("Applying migrations…")
        call_command("migrate", interactive=False)

        if not fixture_path.exists():
            raise CommandError(f"Fixture file not found: {fixture_path}")

        if not options["force"] and Country.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    "Seed data already detected. Skipping fixture load. "
                    "Use --force to reload from the fixture."
                )
            )
            return

        self.stdout.write(f"Loading data from {fixture_path}…")
        call_command("loaddata", str(fixture_path))
        self.stdout.write(self.style.SUCCESS("Seed data loaded successfully."))

