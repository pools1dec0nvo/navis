from django.contrib.gis.db import models
from django.utils import timezone


class Entity(models.Model):
    slug = models.SlugField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, default="#64748b")
    logo = models.ImageField(upload_to="navis/logos/", blank=True, null=True)

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Entity"
        verbose_name_plural = "Entities"

    def __str__(self):
        return self.short_name


class Gateway(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=100)
    location = models.PointField()
    spreading_factor = models.IntegerField(default=9)
    entity = models.ForeignKey(Entity, on_delete=models.PROTECT, related_name="gateways")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    radius = models.PositiveIntegerField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"Gateway {self.identifier} ({self.entity.short_name})"


class Node(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        DEPLOYED = "deployed", "Deployed"
        PROBLEM = "problem", "Problem"
        AFK = "unresponsive", "Unresponsive"
        MAINTENANCE = "maintenance", "Maintenance"

    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=100)
    location = models.PointField()
    parish = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["name"]

    def __str__(self):
         return f"Node {self.identifier} ({self.name})"


class Tank(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    class Issue(models.TextChoices):
        LOW_VOLUME = "empty", "Low Volume"
        PARAM_UNSAFE = "parameter", "Unsafe Parameter"
        PUMP = "pump", "Pump"
        COMMS = "comms", "Undetectable"
        OK = "ok", "Ok!"

    alpha_id = models.CharField(max_length=100)
    capacity = models.FloatField()
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.ACTIVE)
    issue = models.CharField(max_length=30, choices=Issue.choices, default=Issue.OK)
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="tanks")
    last_contacted = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["alpha_id"]

    def __str__(self):
        return f"{self.alpha_id} @ {self.node.identifier} ({self.node.name})"
