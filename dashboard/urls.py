from django.urls import path
from . import views

app_name = "navis"

urlpatterns = [
    path("", views.index, name="index"),
    # Node
    path("node/new/", views.node_create, name="node_create"),
    path("node/<int:pk>/edit/", views.node_edit, name="node_edit"),
    path("node/<int:pk>/delete/", views.node_delete, name="node_delete"),
    # Tank
    path("tank/new/", views.tank_create, name="tank_create"),
    path("tank/<int:pk>/edit/", views.tank_edit, name="tank_edit"),
    path("tank/<int:pk>/delete/", views.tank_delete, name="tank_delete"),
    # Gateway
    path("gateway/new/", views.gateway_create, name="gateway_create"),
    path("gateway/<int:pk>/edit/", views.gateway_edit, name="gateway_edit"),
    path("gateway/<int:pk>/delete/", views.gateway_delete, name="gateway_delete"),
    # Quick-add
    path("node/quickadd/", views.node_quickadd, name="node_quickadd"),
    # Node create with inline tanks
    path("node/new-with-tanks/", views.node_create_with_tanks, name="node_create_with_tanks"),
    # Entity
    path("entity/new/", views.entity_create, name="entity_create"),
    path("entity/<int:pk>/edit/", views.entity_edit, name="entity_edit"),
    path("entity/<int:pk>/delete/", views.entity_delete, name="entity_delete"),
    # Batch reposition
    path("batch-reposition/", views.batch_reposition, name="batch_reposition"),
    # Node inspect
    path("node/<int:pk>/inspect/", views.node_inspect, name="node_inspect"),
]
