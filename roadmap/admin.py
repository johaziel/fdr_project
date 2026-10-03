from django.contrib import admin
from django import forms
from django.utils.html import format_html
from adminsortable2.admin import SortableAdminBase, SortableInlineAdminMixin
from .models import (
    Compagnie, ContactCompagnie, ContactLieu, ContactPrestataire, Deroulement,
    FDR, Hebergement, HebergementFDR, Lieu, Restauration, Transport,
)

def petit_nombre(largeur="4em"):
    return forms.NumberInput(attrs={"min": 0, "style": f"width: {largeur};"})

# --- Lieux, compagnies, hébergements (réutilisables) ---

class ContactLieuInline(SortableInlineAdminMixin, admin.StackedInline):
    model = ContactLieu
    extra = 1

@admin.register(Lieu)
class LieuAdmin(SortableAdminBase, admin.ModelAdmin):
    inlines = [ContactLieuInline]
    list_display = ["apercu_logo", "nom"]
    readonly_fields = ["apercu_logo"]

    @admin.display(description="Logo")
    def apercu_logo(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height:40px;">', obj.logo.url)
        return "—"


class ContactCompagnieInline(SortableInlineAdminMixin, admin.StackedInline):
    model = ContactCompagnie
    extra = 1


@admin.register(Compagnie)
class CompagnieAdmin(SortableAdminBase, admin.ModelAdmin):
    inlines = [ContactCompagnieInline]


@admin.register(Hebergement)
class HebergementAdmin(admin.ModelAdmin):
    search_fields = ["nom"]


# --- La FDR et ses blocs ---

class PrestataireInline(SortableInlineAdminMixin, admin.StackedInline):
    model = ContactPrestataire
    extra = 0

class TransportForm(forms.ModelForm):
    class Meta:
        model = Transport
        fields = "__all__"
        labels = {
            "heure_depart": "Départ",
            "heure_arrivee": "Arrivée",
            "moyen": "Moyen",
            "arrivee": "À",
            "depart": "De",
        }
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "qui": forms.TextInput(attrs={"style": "width: 9em;"}),
            "depart": forms.TextInput(attrs={"style": "width: 9em;"}),
            "arrivee": forms.TextInput(attrs={"style": "width: 9em;"}),
            "heure_depart": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "heure_arrivee": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "note": forms.Textarea(attrs={"rows": 1, "style": "width: 14em;"}),
        }

class TransportInline(admin.TabularInline):
    model = Transport
    form = TransportForm
    extra = 1


class HebergementFDRForm(forms.ModelForm):
    class Meta:
        model = HebergementFDR
        fields = "__all__"
        labels = {
            "distance": "Distance",
            "chambres_single": "Single",
            "chambres_double": "Double",
            "chambres_twin": "Twin",
        }
        widgets = {
            "distance": forms.TextInput(attrs={"style": "width: 8em;"}),
            "chambres_single": petit_nombre("3.5em"),
            "chambres_double": petit_nombre("3.5em"),
            "chambres_twin": petit_nombre("3.5em"),
            "note": forms.Textarea(attrs={"rows": 1, "style": "width: 14em;"}),
        }


class HebergementFDRInline(admin.TabularInline):
    model = HebergementFDR
    form = HebergementFDRForm
    extra = 1


class RestaurationForm(forms.ModelForm):
    class Meta:
        model = Restauration
        fields = "__all__"
        labels = {
            "cie_matin": "Cie matin",
            "cie_midi": "Cie midi",
            "cie_soir": "Cie soir",
            "orga_midi": "Orga midi",
            "orga_soir": "Orga soir",
            "regime": "Régime",
        }
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "cie_matin": petit_nombre(),
            "cie_midi": petit_nombre(),
            "cie_soir": petit_nombre(),
            "orga_midi": petit_nombre(),
            "orga_soir": petit_nombre(),
            "regime": forms.TextInput(attrs={"style": "width: 10em;"}),
            "note": forms.Textarea(attrs={"rows": 1, "style": "width: 12em;"}),
        }


class RestaurationInline(admin.TabularInline):
    model = Restauration
    form = RestaurationForm
    extra = 1

class DeroulementForm(forms.ModelForm):
    class Meta:
        model = Deroulement
        fields = "__all__"
        labels = {
            "date": "Date",
            "heure_debut": "Début",
            "heure_fin": "Fin",
            "mission": "Mission",
            "personel": "Personel",
        }
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "heure_debut": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "heure_fin": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "mission": forms.TextInput(attrs={"style": "width: 20em;"}),
            "personel": forms.TextInput(attrs={"style": "width: 20em;"}),
        }

class DeroulementInline(admin.TabularInline):
    model = Deroulement
    form = DeroulementForm
    extra = 1


@admin.register(FDR)
class FDRAdmin(SortableAdminBase, admin.ModelAdmin):
    list_display = ["spectacle", "compagnie", "date", "date_fin", "lieu", "voir"]
    list_filter = ["date", "compagnie", "lieu"]
    search_fields = ["spectacle", "compagnie__nom", "lieu__nom"]
    date_hierarchy = "date"
    inlines = [
        PrestataireInline, TransportInline, HebergementFDRInline,
        RestaurationInline, DeroulementInline,
    ]
    @admin.display(description="FDR")
    def voir(self, obj):
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">Voir ↗</a>',
            obj.get_absolute_url(),
        )
