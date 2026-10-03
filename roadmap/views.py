from django.views.generic import DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import FDR


class FDRListView(LoginRequiredMixin, ListView):
    model = FDR
    template_name = "roadmap/fdr_list.html"
    context_object_name = "fdrs"

    def get_queryset(self):
        return FDR.objects.select_related("compagnie", "lieu")


class FDRDetailView(LoginRequiredMixin, DetailView):
    model = FDR
    template_name = "roadmap/fdr_detail.html"
    context_object_name = "fdr"

    def get_queryset(self):
        return FDR.objects.select_related("compagnie", "lieu").prefetch_related(
            "lieu__contacts",
            "compagnie__contacts",
            "prestataires",
            "transports",
            "hebergements__hebergement",
            "repas",
            "deroulement",
        )
