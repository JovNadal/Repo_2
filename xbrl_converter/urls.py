from django.contrib import admin
from django.urls import path, include

# API versioning
api_patterns = [
    path("v1/", include("xbrl_mapping.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_patterns)),  # API with versioning
    path("xbrl/", include("xbrl_mapping.urls")),  # Keep original path for backward compatibility
]
