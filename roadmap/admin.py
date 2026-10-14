from django.contrib import admin
from django import forms
from django.utils.html import format_html
from adminsortable2.admin import SortableAdminBase, SortableInlineAdminMixin
from .models import (
    Compagnie, ContactCompagnie, ContactLieu, ContactPrestataire, Deroulement,
    FDR, Hebergement, HebergementFDR, Lieu, Repas, Transport, Spectacle, FichierSpectacle, ContactSpectacle
)
from datetime import timedelta
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme, urlencode

def petit_nombre(largeur="4em"):
    return forms.NumberInput(attrs={"min": 0, "style": f"width: {largeur};"})

# --- Lieux, compagnies, hébergements (réutilisables) ---

class ContactForm(forms.ModelForm):
    class Meta:
        fields = "__all__"
        labels = {
            "telephone": "Tél.",
            "email": "Mail",
        }
        widgets = {
            "nom": forms.TextInput(attrs={"style": "width: 8em;"}),
            "prenom": forms.TextInput(attrs={"style": "width: 8em;"}),
            "fonction": forms.TextInput(attrs={"style": "width: 9em;"}),
            "telephone": forms.TextInput(attrs={"style": "width: 8.5em;"}),
            "email": forms.EmailInput(attrs={"style": "width: 13em;"}),
            "notes": forms.Textarea(attrs={"rows": 1, "style": "width: 12em;"}),
        }

class ContactLieuInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ContactLieu
    form = ContactForm
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

class ContactSpectacleInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ContactSpectacle
    form = ContactForm
    extra = 1


class FichierSpectacleInline(admin.TabularInline):
    model = FichierSpectacle
    extra = 1


@admin.register(Spectacle)
class SpectacleAdmin(SortableAdminBase, admin.ModelAdmin):
    list_display = ["nom", "compagnie", "duree"]
    list_filter = ["compagnie"]
    search_fields = ["nom", "compagnie__nom"]
    inlines = [ContactSpectacleInline, FichierSpectacleInline]

class ContactCompagnieInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ContactCompagnie
    form = ContactForm
    extra = 1


@admin.register(Compagnie)
class CompagnieAdmin(SortableAdminBase, admin.ModelAdmin):
    inlines = [ContactCompagnieInline]


@admin.register(Hebergement)
class HebergementAdmin(admin.ModelAdmin):
    search_fields = ["nom"]


# --- La FDR et ses blocs ---

class PrestataireInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ContactPrestataire
    form = ContactForm
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


class RepasForm(forms.ModelForm):
    class Meta:
        model = Repas
        fields = "__all__"
        labels = {"groupe": "Pour", "lieu": "Lieu / resto", "nombre": "Nb", "regime": "Régime"}
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "lieu": forms.TextInput(attrs={"style": "width: 11em;"}),
            "nombre": petit_nombre("4em"),
            "regime": forms.TextInput(attrs={"style": "width: 9em;"}),
            "note": forms.Textarea(attrs={"rows": 1, "style": "width: 10em;"}),
        }

class RepasInline(admin.TabularInline):
    model = Repas
    form = RepasForm
    extra = 0


class DeroulementForm(forms.ModelForm):
    class Meta:
        model = Deroulement
        fields = "__all__"
        labels = {
            "date": "Date",
            "heure_debut": "Début",
            "heure_fin": "Fin",
            "mission": "Mission",
            "personel": "Personnel",
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


class FDRForm(forms.ModelForm):
    class Meta:
        model = FDR
        fields = "__all__"
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "date_fin": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

class RetourFrontMixin:
    """Équivalent du ?destination= de Drupal : après un enregistrement,
    retourne à l'URL donnée par ?next= (uniquement sur ce site)."""

    def _cible_retour(self, request):
        cible = request.GET.get("next")
        if cible and url_has_allowed_host_and_scheme(
            cible, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return cible
        return None

    def _traiter_retour(self, request, response):
        cible = self._cible_retour(request)
        if not cible or not isinstance(response, HttpResponseRedirect):
            return response
        if "_save" in request.POST:  # bouton « Enregistrer » simple
            return HttpResponseRedirect(cible)
        if "_continue" in request.POST:  # « Enregistrer et continuer » : on garde next
            sep = "&" if "?" in response.url else "?"
            return HttpResponseRedirect(f"{response.url}{sep}{urlencode({'next': cible})}")
        return response

    def response_change(self, request, obj):
        return self._traiter_retour(request, super().response_change(request, obj))

    def response_add(self, request, obj, post_url_continue=None):
        return self._traiter_retour(request, super().response_add(request, obj, post_url_continue))


@admin.register(FDR)
class FDRAdmin(RetourFrontMixin, SortableAdminBase, admin.ModelAdmin):
    list_display = ["voir", "statut", "type", "spectacle", "compagnie", "date", "date_fin", "lieu"]
    list_display_links = ["spectacle"]
    list_filter = ["statut", "type", "date", "compagnie", "lieu"]
    search_fields = ["spectacle__nom", "compagnie__nom", "lieu__nom"]
    list_select_related = ["compagnie", "lieu", "spectacle"]
    date_hierarchy = "date"
    form = FDRForm
    save_as = True
    inlines = [
        PrestataireInline, TransportInline, HebergementFDRInline,
        RepasInline, DeroulementInline,
    ]
    @admin.display(description="FDR")
    def voir(self, obj):
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">↗</a>',
            obj.get_absolute_url(),
        )
    def get_inline_instances(self, request, obj=None):
        instances = super().get_inline_instances(request, obj)
        if obj is not None:  # édition d'une FDR existante
            for inline in instances:
                inline.classes = ["collapse"]
        return instances
    
    actions = ["marquer_envoye", "marquer_valide", "generer_repas"]

    @admin.action(description="Marquer comme envoyé")
    def marquer_envoye(self, request, queryset):
        queryset.update(statut=FDR.Statut.ENVOYE)

    @admin.action(description="Marquer comme validé")
    def marquer_valide(self, request, queryset):
        queryset.update(statut=FDR.Statut.VALIDE)

    @admin.action(description="Générer la grille de repas (jours de la FDR)")
    def generer_repas(self, request, queryset):
        modeles = [("matin", "cie"), ("midi", "cie"), ("midi", "orga"),
                   ("soir", "cie"), ("soir", "orga")]
        crees = 0
        for fdr in queryset:
            existants = set(fdr.repas.values_list("date", "moment", "groupe"))
            jour, fin = fdr.date, (fdr.date_fin or fdr.date)
            while jour <= fin:
                for moment, groupe in modeles:
                    if (jour, moment, groupe) not in existants:
                        Repas.objects.create(fdr=fdr, date=jour, moment=moment, groupe=groupe)
                        crees += 1
                jour += timedelta(days=1)
        self.message_user(request, f"{crees} ligne(s) de repas créée(s) : renseigne les nombres.")
