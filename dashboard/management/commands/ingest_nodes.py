import csv
import math
import os

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from navis.dashboard.models import Node, Tank


class Command(BaseCommand):
    help = "Ingest nodes.csv to populate Node and Tank models."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            default=None,
            help="Path to CSV file (default: navis/nodes.csv inside BASE_DIR)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be created without writing to DB",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Skip rows whose node identifier already exists",
        )

    def handle(self, *args, **options):
        csv_path = options["csv"] or os.path.join(
            settings.BASE_DIR, "navis", "nodes.csv"
        )
        if not os.path.exists(csv_path):
            raise CommandError(f"CSV file not found: {csv_path}")

        dry_run = options["dry_run"]
        skip_existing = options["skip_existing"]

        RADIUS_M = 5.0
        node_count = 0
        tank_count_total = 0

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no DB writes\n"))

        try:
            with transaction.atomic():
                for row in rows:
                    identifier = row["node_id"].strip()
                    name = row["name"].strip()
                    parish = row["parish"].strip()
                    lat = float(row["latitude"])
                    lng = float(row["longitude"])
                    tank_prefix = row["tank_prefix"].strip()
                    n = int(row["tank_count"])

                    if skip_existing and Node.objects.filter(identifier=identifier).exists():
                        self.stdout.write(f"  SKIP {identifier} (already exists)")
                        continue

                    if dry_run:
                        self.stdout.write(
                            f"  NODE {identifier!r} | {name!r} | {parish!r} | "
                            f"({lat}, {lng}) | {n} tanks"
                        )
                        for i in range(n):
                            suffix = chr(ord("A") + i)
                            alpha_id = f"{tank_prefix}{suffix}"
                            self.stdout.write(f"    TANK {alpha_id}")
                        node_count += 1
                        tank_count_total += n
                        continue

                    node = Node.objects.create(
                        name=name,
                        identifier=identifier,
                        parish=parish,
                        location=Point(lng, lat),
                        status="active",
                    )

                    dlat = RADIUS_M / 111_320
                    dlng = RADIUS_M / (111_320 * math.cos(math.radians(lat)))

                    for i in range(n):
                        suffix = chr(ord("A") + i)
                        alpha_id = f"{tank_prefix}{suffix}"
                        angle = 2 * math.pi * i / n
                        tlat = lat + dlat * math.sin(angle)
                        tlng = lng + dlng * math.cos(angle)
                        Tank.objects.create(
                            alpha_id=alpha_id,
                            capacity=1000,
                            status="active",
                            issue="ok",
                            node=node,
                            location=Point(tlng, tlat),
                        )

                    node_count += 1
                    tank_count_total += n

                if dry_run:
                    raise transaction.TransactionManagementError("dry-run rollback")

        except transaction.TransactionManagementError:
            pass  # expected dry-run rollback

        verb = "Would create" if dry_run else "Created"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} {node_count} nodes and {tank_count_total} tanks."
            )
        )
