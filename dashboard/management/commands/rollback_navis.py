from django.core.management.base import BaseCommand
from django.db import connection

from navis.dashboard.models import Node, Tank


class Command(BaseCommand):
    help = "Delete all Node and Tank records and reset their ID sequences."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip confirmation prompt",
        )

    def handle(self, *args, **options):
        node_count = Node.objects.count()
        tank_count = Tank.objects.count()

        if not options["yes"]:
            confirm = input(
                f"This will delete {tank_count} tanks and {node_count} nodes. "
                "Type 'yes' to confirm: "
            )
            if confirm.strip().lower() != "yes":
                self.stdout.write("Aborted.")
                return

        Tank.objects.all().delete()
        Node.objects.all().delete()

        with connection.cursor() as c:
            c.execute("ALTER SEQUENCE navis_node_id_seq RESTART WITH 1")
            c.execute("ALTER SEQUENCE navis_tank_id_seq RESTART WITH 1")

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {tank_count} tanks and {node_count} nodes. Sequences reset."
            )
        )
