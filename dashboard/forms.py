from django import forms
from django.contrib.gis.geos import Point

from .models import Entity, Gateway, Node, Tank


class NodeForm(forms.ModelForm):
    lat = forms.FloatField(widget=forms.HiddenInput(), required=False)
    lng = forms.FloatField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Node
        fields = ["name", "identifier", "status", "parish"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        lat = self.cleaned_data.get("lat")
        lng = self.cleaned_data.get("lng")
        if lat is not None and lng is not None:
            instance.location = Point(lng, lat)
        if commit:
            instance.save()
        return instance


class TankForm(forms.ModelForm):
    class Meta:
        model = Tank
        fields = ["alpha_id", "capacity", "status", "issue", "node"]


class GatewayForm(forms.ModelForm):
    lat = forms.FloatField(widget=forms.HiddenInput(), required=False)
    lng = forms.FloatField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Gateway
        fields = ["name", "identifier", "spreading_factor", "entity", "status", "radius"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        lat = self.cleaned_data.get("lat")
        lng = self.cleaned_data.get("lng")
        if lat is not None and lng is not None:
            instance.location = Point(lng, lat)
        if commit:
            instance.save()
        return instance


class EntityForm(forms.ModelForm):
    class Meta:
        model = Entity
        fields = ["slug", "full_name", "short_name", "description", "color"]
