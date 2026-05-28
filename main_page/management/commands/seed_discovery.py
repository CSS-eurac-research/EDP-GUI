"""
Local-development helper.

Bulk-imports public EDP GeoNetwork records into the local
``GeonetworkMetadata`` table by calling the GeoNetwork Elasticsearch
search endpoint.

The legacy admin action ``download_all_metadata`` in ``main_page.admin``
targets the deprecated ``/srv/eng/q`` endpoint (now returns
``UnsupportedOperationException: Use ES search instead``). This command
is intentionally additive: it does not modify ``admin.py`` and can be
removed (or wired into the admin action) once the official harvester is
rewritten.

Examples:
    docker compose exec web python manage.py seed_discovery
    docker compose exec web python manage.py seed_discovery --limit 50
    docker compose exec web python manage.py seed_discovery --reset
    docker compose exec web python manage.py seed_discovery --query snow
    docker compose exec web python manage.py seed_discovery --batch-size 50
    docker compose exec web python manage.py seed_discovery --dry-run
"""
import json

import requests
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime

from main_page.models import GeonetworkMetadata


DEFAULT_ES_URL = (
    "https://edp-portal.eurac.edu/geonetwork/srv/api/search/records/_search"
)
DEFAULT_BATCH = 100


class Command(BaseCommand):
    help = (
        "Import GeoNetwork metadata records into the local GeonetworkMetadata "
        "table from the public EDP Elasticsearch search endpoint."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            default=DEFAULT_ES_URL,
            help="GeoNetwork Elasticsearch _search endpoint URL.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of records to import (default: all).",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=DEFAULT_BATCH,
            help="Records per page (default: %(default)s, max 1000).",
        )
        parser.add_argument(
            "--query",
            default=None,
            help='Optional query_string text (default: match_all).',
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all rows in GeonetworkMetadata before importing.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch and parse records, but do not write to the database.",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=30,
            help="HTTP request timeout in seconds (default: %(default)s).",
        )

    def handle(self, *args, **opts):
        url = opts["url"]
        limit = opts["limit"]
        batch = max(1, min(opts["batch_size"], 1000))
        query_text = opts["query"]
        reset = opts["reset"]
        dry_run = opts["dry_run"]
        timeout = opts["timeout"]

        if reset and not dry_run:
            removed = GeonetworkMetadata.objects.count()
            GeonetworkMetadata.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                "Cleared GeonetworkMetadata ({0} rows).".format(removed)
            ))

        query = (
            {"query_string": {"query": query_text}}
            if query_text
            else {"match_all": {}}
        )

        total_seen = 0
        created = 0
        updated = 0
        skipped = 0
        from_index = 0

        while True:
            page_size = batch
            if limit is not None:
                remaining = limit - total_seen
                if remaining <= 0:
                    break
                page_size = min(page_size, remaining)

            payload = {
                "from": from_index,
                "size": page_size,
                "query": query,
            }

            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    timeout=timeout,
                )
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as exc:
                raise CommandError("Request failed: {0}".format(exc)) from exc

            hits = (data.get("hits") or {}).get("hits") or []
            total_reported = (
                (data.get("hits") or {}).get("total") or {}
            ).get("value", "?")

            if not hits:
                break

            for hit in hits:
                source = hit.get("_source") or {}
                try:
                    fields = self._map_source(source)
                except Exception as exc:  # noqa: BLE001
                    skipped += 1
                    self.stderr.write(
                        "  skip {0}: {1}".format(hit.get("_id", "?"), exc)
                    )
                    continue

                uuid = fields.pop("uuid", None)
                if not uuid:
                    skipped += 1
                    continue

                if dry_run:
                    total_seen += 1
                    continue

                _, was_created = GeonetworkMetadata.objects.update_or_create(
                    uuid=uuid,
                    defaults=fields,
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

                total_seen += 1

            self.stdout.write(
                "  page from={0:>4} size={1:>3} | "
                "created={2} updated={3} skipped={4} "
                "(total reported: {5})".format(
                    from_index, len(hits), created, updated, skipped,
                    total_reported,
                )
            )

            from_index += len(hits)
            if len(hits) < page_size:
                break

        summary = (
            "Done. seen={0} created={1} updated={2} skipped={3}".format(
                total_seen, created, updated, skipped,
            )
        )
        if dry_run:
            summary = "[DRY RUN] " + summary
        self.stdout.write(self.style.SUCCESS(summary))

    # -- mapping helpers ---------------------------------------------------

    def _map_source(self, source):
        """Map an ES ``_source`` dict to ``GeonetworkMetadata`` defaults."""
        uuid = source.get("metadataIdentifier") or source.get("uuid")

        title = self._object_default(source.get("resourceTitleObject"))
        abstract = self._object_default(source.get("resourceAbstractObject"))
        supplemental = self._object_default(
            source.get("supplementalInformationObject")
        )
        name_collection = self._object_default(
            source.get("OrgForResourceObject")
        )

        cat_list = source.get("cat") or []
        category = cat_list[0] if cat_list else None

        tags = source.get("tag") or []
        keyword = ",".join(
            t.get("default")
            for t in tags
            if isinstance(t, dict) and t.get("default")
        )

        overview = source.get("overview") or []
        thumbnail = ""
        for item in overview:
            url = (item or {}).get("url")
            if url:
                thumbnail = url
                break

        cl_topic = self._first_default(source.get("cl_topic"))
        presentation = self._first_default(source.get("cl_presentationForm"))

        doi = None
        for ident in source.get("resourceIdentifier") or []:
            if not isinstance(ident, dict):
                continue
            link = ident.get("link") or ""
            code = ident.get("code") or ""
            if "doi" in (link + code).lower():
                doi = link or code
                break

        period_begin = period_end = None
        ranges = source.get("resourceTemporalDateRange") or []
        if ranges and isinstance(ranges[0], dict):
            period_begin = self._parse_dt(ranges[0].get("gte"))
            period_end = self._parse_dt(ranges[0].get("lte"))

        last_update = self._parse_dt(
            source.get("dateStamp")
            or source.get("changeDate")
            or source.get("indexingDate")
        )

        geom = self._parse_geom(source.get("geom"))

        return {
            "uuid": uuid,
            "title": self._clip(title, 500),
            "abstract": abstract or None,
            "category": self._clip(category, 500),
            "keyword": self._clip(keyword, 1000),
            "thumbnail": self._clip(thumbnail, 1000),
            "geom": geom,
            "last_update": last_update,
            "period_begin": period_begin,
            "period_end": period_end,
            "doi": self._clip(doi, 500),
            "name_collection": self._clip(name_collection, 500),
            "cl_topic": self._clip(cl_topic, 500),
            "presentation_form": self._clip(presentation, 500),
            "supplemental_information": supplemental or None,
        }

    @staticmethod
    def _clip(value, length):
        if not value:
            return None
        text = str(value)
        return text[:length] or None

    @staticmethod
    def _object_default(value):
        """ES localised object fields: ``{"default": "...", "langeng": "..."}``."""
        if isinstance(value, dict):
            return value.get("default") or value.get("langeng") or ""
        return ""

    @staticmethod
    def _first_default(items):
        for item in items or []:
            if not isinstance(item, dict):
                continue
            value = item.get("default") or item.get("langeng")
            if value:
                return value
        return None

    @staticmethod
    def _parse_dt(value):
        if not value or not isinstance(value, str):
            return None
        normalized = value.replace("Z", "+00:00")
        try:
            return parse_datetime(normalized)
        except (ValueError, TypeError):
            return None

    def _parse_geom(self, geom):
        """Return a Django GEOS Polygon (srid=4326), or ``None``.

        GeoNetwork sometimes returns MultiPolygon/Point/etc. Our model field
        is ``PolygonField`` so any non-polygon geometry is reduced to its
        axis-aligned bounding box (envelope).
        """
        if not geom:
            return None
        try:
            geos_geom = GEOSGeometry(json.dumps(geom), srid=4326)
        except (ValueError, TypeError, Exception) as exc:  # noqa: BLE001
            self.stderr.write("  geom parse error: {0}".format(exc))
            return None

        if geos_geom.geom_type == "Polygon":
            return geos_geom
        try:
            envelope = geos_geom.envelope
            if envelope.geom_type == "Polygon":
                return envelope
        except Exception as exc:  # noqa: BLE001
            self.stderr.write("  geom envelope error: {0}".format(exc))
        return None
