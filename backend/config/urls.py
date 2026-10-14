from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

urlpatterns = [
    path("api/v1/", include("caef.urls")),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
]
