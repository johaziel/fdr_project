from django.views.generic import DetailView, ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import FDR, Spectacle
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse


class FDRListView(LoginRequiredMixin, ListView):
    model = FDR
    template_name = "roadmap/fdr_list.html"
    context_object_name = "fdrs"

    def get_queryset(self):
        return FDR.objects.select_related("compagnie", "lieu", "spectacle")


class FDRDetailView(LoginRequiredMixin, DetailView):
    model = FDR
    template_name = "roadmap/fdr_detail.html"
    context_object_name = "fdr"

    def get_queryset(self):
        return FDR.objects.select_related("compagnie", "lieu", "spectacle").prefetch_related(
            "lieu__contacts",
            "compagnie__contacts",
            "prestataires",
            "transports",
            "hebergements__hebergement",
            "repas",
            "deroulement",
            "spectacle__contacts",
            "spectacle__fichiers"
        )

class SpectacleListView(LoginRequiredMixin, ListView):
    model = Spectacle
    template_name = "roadmap/spectacle_list.html"
    context_object_name = "spectacles"

    def get_queryset(self):
        return Spectacle.objects.select_related("compagnie")

class SpectacleDetailView(LoginRequiredMixin, DetailView):
    model = Spectacle
    template_name = "roadmap/spectacle_detail.html"
    context_object_name = "spectacle"

    def get_queryset(self):
        return Spectacle.objects.select_related("compagnie").prefetch_related(
            "contacts", "fichiers", "fdrs__lieu"
        )


class CalendrierView(TemplateView):  # ajoute LoginRequiredMixin si tes autres vues l'utilisent
    template_name = "roadmap/calendrier.html"

STATUT_COULEURS = {
    # statut: (fond, bordure, texte)
    "brouillon": ("#eef0f3", "#9ca3af", "#374151"),
    "envoye": ("#fff3d6", "#e0a100", "#7a4e00"),
    "valide": ("#dcf3e3", "#2e9e5b", "#15572f"),
}

@login_required
def calendrier_events(request):
    """Flux JSON lu par FullCalendar (paramètres GET : start et end)."""
    try:
        debut = date.fromisoformat(request.GET["start"][:10])
        fin = date.fromisoformat(request.GET["end"][:10])
    except (KeyError, ValueError):
        return JsonResponse([], safe=False, status=400)

    fdrs = (
        FDR.objects.select_related("compagnie", "lieu", "spectacle")
        .filter(date__lt=fin)
        .filter(Q(date_fin__gte=debut) | Q(date_fin__isnull=True, date__gte=debut))
    )

    evenements = []
    for fdr in fdrs:
        fond, bordure, texte = STATUT_COULEURS.get(fdr.statut, STATUT_COULEURS["brouillon"])
        evenements.append({
            "id": fdr.pk,
            "title": str(fdr.spectacle),
            "start": fdr.date.isoformat(),
            # FullCalendar attend une fin exclusive : on ajoute un jour
            "end": ((fdr.date_fin or fdr.date) + timedelta(days=1)).isoformat(),
            "allDay": True,
            "url": fdr.get_absolute_url(),
            "backgroundColor": fond,
            "borderColor": bordure,
            "textColor": texte,
            "extendedProps": {
                "compagnie": str(fdr.compagnie),
                "lieu": str(fdr.lieu),
                "heure": fdr.heure,
                "statut": fdr.get_statut_display(),
            },
        })
    return JsonResponse(evenements, safe=False)