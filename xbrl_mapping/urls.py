# urls.py (updated)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'xbrl', views.PartialXBRLViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('upload/', views.upload_xbrl_json, name='upload-xbrl'),
    path('uen/<str:uen>/', views.get_xbrl_by_uen, name='get-xbrl-by-uen'),
    path('direct-import/', views.direct_json_import, name='direct-json-import'),
    path('export/<int:pk>/', views.export_xbrl_json, name='export-xbrl-json'),
    path('validate/', views.validate_xbrl_json, name='validate-xbrl-json'),
    path('template/', views.get_xbrl_template, name='get-xbrl-template'),
    path('bulk/', views.bulk_operations, name='bulk-operations'),
    path('mapping-input/', views.MappingInputView.as_view(), name='mapping-input'),
    path('mapping-input/<uuid:mapping_id>/', views.MappingInputView.as_view(), name='get-mapping-input'),
]