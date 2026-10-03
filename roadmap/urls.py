from django.urls import path

from . import views

app_name = "roadmap"

urlpatterns = [
    path("", views.FDRListView.as_view(), name="list"),
    path("fdr/<int:pk>/", views.FDRDetailView.as_view(), name="detail"),
]
