import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from .forms import EntityForm, GatewayForm, NodeForm, TankForm
from .models import Entity, Gateway, Node, Tank


def _build_geojson(nodes, gateways):
    features = []
    for gw in gateways:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [gw.location.x, gw.location.y]},
            "properties": {
                "id": gw.id,
                "kind": "gateway",
                "label": gw.identifier,
                "name": gw.name,
                "status": gw.status,
                "radius": gw.radius,
                "spreading_factor": gw.spreading_factor,
                "entity_id": gw.entity_id,
                "entity_name": gw.entity.short_name,
                "entity_full_name": gw.entity.full_name,
                "entity_color": gw.entity.color,
                "entity_logo": gw.entity.logo.url if gw.entity.logo else None,
            },
        })
    for node in nodes:
        node_coords = [node.location.x, node.location.y]
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": node_coords},
            "properties": {
                "id": node.id,
                "kind": "node",
                "label": node.identifier,
                "name": node.name,
                "status": node.status,
                "parish": node.parish,
                "tank_count": node.tanks.count(),
            },
        })
        for tank in node.tanks.all():
            features.append({
                "type": "Feature",
                "geometry": None,
                "properties": {
                    "id": tank.id,
                    "kind": "tank",
                    "label": tank.alpha_id,
                    "capacity": tank.capacity,
                    "status": tank.status,
                    "issue": tank.issue,
                    "node_id": node.id,
                    "parish": node.parish,
                    "last_contacted": tank.last_contacted.isoformat() if tank.last_contacted else None,
                },
            })
    return json.dumps({"type": "FeatureCollection", "features": features})


@login_required
def index(request):
    nodes = Node.objects.prefetch_related("tanks").all()
    gateways = Gateway.objects.select_related("entity").all()
    entities = Entity.objects.all()
    parishes = sorted({n.parish for n in nodes if n.parish})
    lc = settings.LEAFLET_CONFIG
    center = lc["DEFAULT_CENTER"]
    return render(request, "navis/index.html", {
        "geojson": _build_geojson(nodes, gateways),
        "nodes": nodes,
        "gateways": gateways,
        "entities": entities,
        "parishes": parishes,
        "map_lat": center[0],
        "map_lng": center[1],
        "map_zoom": lc["DEFAULT_ZOOM"],
    })


# ── Node ──────────────────────────────────────────────────────────────────────

@login_required
@require_http_methods(["POST"])
def node_create(request):
    form = NodeForm(request.POST)
    if form.is_valid():
        node = form.save()
        return JsonResponse({"ok": True, "id": node.id, "identifier": node.identifier,
                             "name": node.name, "status": node.status,
                             "lat": node.location.y, "lng": node.location.x})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)


@login_required
@require_http_methods(["GET", "POST"])
def node_edit(request, pk):
    node = get_object_or_404(Node, pk=pk)
    if request.method == "POST":
        form = NodeForm(request.POST, instance=node)
        if form.is_valid():
            form.save()
            return JsonResponse({"ok": True})
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    return JsonResponse({
        "id": node.id, "name": node.name, "identifier": node.identifier,
        "status": node.status, "parish": node.parish,
        "lat": node.location.y, "lng": node.location.x,
    })


@login_required
@require_http_methods(["POST"])
def node_delete(request, pk):
    get_object_or_404(Node, pk=pk).delete()
    return JsonResponse({"ok": True})


# ── Tank ──────────────────────────────────────────────────────────────────────

@login_required
@require_http_methods(["POST"])
def tank_create(request):
    form = TankForm(request.POST)
    if form.is_valid():
        tank = form.save()
        node = tank.node
        return JsonResponse({"ok": True, "id": tank.id, "alpha_id": tank.alpha_id,
                             "capacity": tank.capacity, "status": tank.status, "issue": tank.issue,
                             "node_id": node.id})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)


@login_required
@require_http_methods(["GET", "POST"])
def tank_edit(request, pk):
    tank = get_object_or_404(Tank, pk=pk)
    if request.method == "POST":
        form = TankForm(request.POST, instance=tank)
        if form.is_valid():
            form.save()
            return JsonResponse({"ok": True})
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    return JsonResponse({
        "id": tank.id, "alpha_id": tank.alpha_id, "capacity": tank.capacity,
        "status": tank.status, "issue": tank.issue, "node_id": tank.node_id,
    })


@login_required
@require_http_methods(["POST"])
def tank_delete(request, pk):
    get_object_or_404(Tank, pk=pk).delete()
    return JsonResponse({"ok": True})


# ── Gateway ───────────────────────────────────────────────────────────────────

@login_required
@require_http_methods(["POST"])
def gateway_create(request):
    form = GatewayForm(request.POST)
    if form.is_valid():
        gw = form.save()
        return JsonResponse({
            "ok": True, "id": gw.id, "name": gw.name, "identifier": gw.identifier,
            "status": gw.status, "radius": gw.radius, "spreading_factor": gw.spreading_factor,
            "entity_id": gw.entity_id, "entity_name": gw.entity.short_name,
            "entity_full_name": gw.entity.full_name,
            "entity_color": gw.entity.color,
            "entity_logo": gw.entity.logo.url if gw.entity.logo else None,
            "lat": gw.location.y, "lng": gw.location.x,
        })
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)


@login_required
@require_http_methods(["GET", "POST"])
def gateway_edit(request, pk):
    gw = get_object_or_404(Gateway, pk=pk)
    if request.method == "POST":
        form = GatewayForm(request.POST, instance=gw)
        if form.is_valid():
            form.save()
            return JsonResponse({"ok": True})
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    return JsonResponse({
        "id": gw.id, "name": gw.name, "identifier": gw.identifier,
        "status": gw.status, "radius": gw.radius, "spreading_factor": gw.spreading_factor,
        "entity_id": gw.entity_id,
        "lat": gw.location.y, "lng": gw.location.x,
    })


@login_required
@require_http_methods(["POST"])
def gateway_delete(request, pk):
    get_object_or_404(Gateway, pk=pk).delete()
    return JsonResponse({"ok": True})


# ── Entity ────────────────────────────────────────────────────────────────────

@login_required
@require_http_methods(["POST"])
def entity_create(request):
    form = EntityForm(request.POST, request.FILES)
    if form.is_valid():
        entity = form.save()
        return JsonResponse({
            "ok": True, "id": entity.id, "slug": entity.slug,
            "short_name": entity.short_name, "full_name": entity.full_name,
            "color": entity.color,
        })
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)


@login_required
@require_http_methods(["GET", "POST"])
def entity_edit(request, pk):
    entity = get_object_or_404(Entity, pk=pk)
    if request.method == "POST":
        form = EntityForm(request.POST, request.FILES, instance=entity)
        if form.is_valid():
            form.save()
            return JsonResponse({"ok": True})
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    return JsonResponse({
        "id": entity.id, "slug": entity.slug, "short_name": entity.short_name,
        "full_name": entity.full_name, "description": entity.description,
        "color": entity.color,
    })


@login_required
@require_http_methods(["POST"])
def entity_delete(request, pk):
    get_object_or_404(Entity, pk=pk).delete()
    return JsonResponse({"ok": True})


# ── Quick-add (node + N tanks around it) ─────────────────────────────────────

@login_required
@require_http_methods(["POST"])
def node_quickadd(request):
    """
    Create a node at (lat, lng) plus N tanks arranged in a circle of 3 m radius.
    POST fields: lat, lng, identifier, name, status,
                 tank_count, tank_capacity, tank_prefix
    Alpha IDs are generated as <prefix>A, <prefix>B, … (wrapping with AA, AB… after Z)
    """
    try:
        lat = float(request.POST["lat"])
        lng = float(request.POST["lng"])
        n   = int(request.POST.get("tank_count", 1))
        if n < 1 or n > 26:
            return JsonResponse({"ok": False, "errors": {"tank_count": ["Must be 1–26"]}}, status=400)
    except (KeyError, ValueError):
        return JsonResponse({"ok": False, "errors": {"__all__": ["Invalid coordinates or count"]}}, status=400)

    node_form = NodeForm({
        "identifier": request.POST.get("identifier", ""),
        "name":       request.POST.get("name", ""),
        "status":     request.POST.get("status", "active"),
        "lat": lat, "lng": lng,
    })
    if not node_form.is_valid():
        return JsonResponse({"ok": False, "errors": node_form.errors}, status=400)
    node = node_form.save()

    prefix   = request.POST.get("tank_prefix", "TK-")
    capacity = request.POST.get("tank_capacity", "0")

    tanks_out = []
    for i in range(n):
        suffix = chr(ord("A") + i)
        tank   = Tank.objects.create(
            alpha_id=f"{prefix}{suffix}",
            capacity=float(capacity),
            status="active",
            issue="ok",
            node=node,
        )
        tanks_out.append({
            "id": tank.id, "alpha_id": tank.alpha_id, "capacity": tank.capacity,
            "status": tank.status, "issue": tank.issue,
            "node_id": node.id,
        })

    return JsonResponse({
        "ok": True,
        "node": {
            "id": node.id, "identifier": node.identifier, "name": node.name,
            "status": node.status, "lat": node.location.y, "lng": node.location.x,
        },
        "tanks": tanks_out,
    })


# ── Node create with inline tanks ─────────────────────────────────────────────

@login_required
@require_http_methods(["POST"])
def node_create_with_tanks(request):
    """Create a node plus inline tanks from a JSON body."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "errors": {"__all__": ["Invalid JSON"]}}, status=400)

    node_form = NodeForm({
        "identifier": data.get("identifier", ""),
        "name": data.get("name", ""),
        "status": data.get("status", "active"),
        "parish": data.get("parish", ""),
        "lat": data.get("lat"),
        "lng": data.get("lng"),
    })
    if not node_form.is_valid():
        return JsonResponse({"ok": False, "errors": node_form.errors}, status=400)

    with transaction.atomic():
        node = node_form.save()
        tanks_out = []
        for t in data.get("tanks", []):
            tank = Tank.objects.create(
                alpha_id=t.get("alpha_id", ""),
                capacity=float(t.get("capacity", 100)),
                status="active",
                issue="ok",
                node=node,
            )
            tanks_out.append({
                "id": tank.id, "alpha_id": tank.alpha_id,
                "capacity": tank.capacity, "status": tank.status,
                "issue": tank.issue, "node_id": node.id,
            })

    return JsonResponse({
        "ok": True,
        "node": {
            "id": node.id, "identifier": node.identifier, "name": node.name,
            "status": node.status, "parish": node.parish,
            "lat": node.location.y, "lng": node.location.x,
        },
        "tanks": tanks_out,
    })


# ── Batch reposition ──────────────────────────────────────────────────────────

@login_required
@require_http_methods(["POST"])
def batch_reposition(request):
    """Update locations for multiple nodes/gateways in one request."""
    data = json.loads(request.body)
    for item in data.get("items", []):
        point = Point(float(item["lng"]), float(item["lat"]))
        if item["kind"] == "node":
            Node.objects.filter(pk=item["id"]).update(location=point)
        elif item["kind"] == "gateway":
            Gateway.objects.filter(pk=item["id"]).update(location=point)
    return JsonResponse({"ok": True})


# ── Node inspect ──────────────────────────────────────────────────────────────

@login_required
@require_http_methods(["GET"])
def node_inspect(request, pk):
    """Return node + tanks + nearest gateway for the inspect overlay."""
    node = get_object_or_404(Node, pk=pk)
    tanks = []
    for t in node.tanks.all():
        tanks.append({
            "id": t.id,
            "alpha_id": t.alpha_id,
            "capacity": t.capacity,
            "status": t.status,
            "issue": t.issue,
            "last_contacted": t.last_contacted.isoformat() if t.last_contacted else None,
        })
    nearest_gw = None
    if Gateway.objects.exists():
        gw = Gateway.objects.select_related("entity").annotate(
            dist=Distance("location", node.location)
        ).order_by("dist").first()
        if gw:
            nearest_gw = {
                "identifier": gw.identifier,
                "entity_short_name": gw.entity.short_name,
            }
    return JsonResponse({
        "node": {
            "id": node.id, "identifier": node.identifier, "name": node.name,
            "status": node.status, "lat": node.location.y, "lng": node.location.x,
        },
        "tanks": tanks,
        "nearest_gateway": nearest_gw,
    })
