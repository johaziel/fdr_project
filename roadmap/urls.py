from django.urls import path

from . import views

app_name = "roadmap"

urlpatterns = [
    path("", views.FDRListView.as_view(), name="list"),
    path("fdr/<int:pk>/", views.FDRDetailView.as_view(), name="detail"),
    path("spectacle/", views.SpectacleListView.as_view(), name="spectacle_list"),
    path("spectacle/<int:pk>/", views.SpectacleDetailView.as_view(), name="spectacle_detail"),
    path("calendrier/", views.CalendrierView.as_view(), name="calendrier"),
    path("calendrier/events/", views.calendrier_events, name="calendrier_events"),
]
