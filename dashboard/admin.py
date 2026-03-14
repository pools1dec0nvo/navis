from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Entity, Gateway, Node, Tank


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ["short_name", "full_name", "slug", "color"]
    prepopulated_fields = {"slug": ("short_name",)}
    search_fields = ["short_name", "full_name", "slug"]


class GatewayInline(admin.TabularInline):
    model = Gateway
    extra = 0
    fields = ["name", "identifier", "status", "spreading_factor", "radius"]
    show_change_link = True


@admin.register(Gateway)
class GatewayAdmin(GISModelAdmin):
    list_display = ["name", "identifier", "entity", "status", "spreading_factor", "radius"]
    list_filter = ["status", "entity"]
    search_fields = ["name", "identifier"]
    autocomplete_fields = ["entity"]


class TankInline(admin.TabularInline):
    model = Tank
    extra = 0
    fields = ["alpha_id", "capacity", "status", "issue", "last_contacted"]
    show_change_link = True


@admin.register(Node)
class NodeAdmin(GISModelAdmin):
    list_display = ["name", "identifier", "status"]
    list_filter = ["status"]
    search_fields = ["name", "identifier"]
    inlines = [TankInline]


@admin.register(Tank)
class TankAdmin(GISModelAdmin):
    list_display = ["alpha_id", "node", "capacity", "status", "issue", "last_contacted"]
    list_filter = ["status", "issue"]
    search_fields = ["alpha_id", "node__name"]
    autocomplete_fields = ["node"]
