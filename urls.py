# ============================================================================
# urls.py - Routes API principales
# ============================================================================

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from .views import (
    ChantiersViewSet, LotsViewSet, TachesViewSet,
    HeuresTravailViewSet, EquipesViewSet, MembresViewSet,
    SousTraitantsViewSet, AnomaliesViewSet
)

# ============================================================================
# Router DRF - Enregistrement automatique des ViewSets
# ============================================================================
router = DefaultRouter()

# Endpoints principaux
router.register(r'chantiers', ChantiersViewSet, basename='chantier')
router.register(r'lots', LotsViewSet, basename='lot')
router.register(r'taches', TachesViewSet, basename='tache')
router.register(r'heures_travail', HeuresTravailViewSet, basename='heures')
router.register(r'equipes', EquipesViewSet, basename='equipe')
router.register(r'membres', MembresViewSet, basename='membre')
router.register(r'sous_traitants', SousTraitantsViewSet, basename='soustraitant')
router.register(r'anomalies', AnomaliesViewSet, basename='anomalie')

# ============================================================================
# URLs patterns
# ============================================================================
urlpatterns = [
    # Router automatique
    path('', include(router.urls)),
    
    # Endpoints de documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), 
         name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), 
         name='redoc'),
]

# ============================================================================
# URLs principales (à inclure dans config/urls.py)
# ============================================================================
# 
# Dans config/urls.py :
#
# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static
#
# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('api/v1/', include('chantiers.urls')),
#     path('api/auth/', include('rest_framework.urls')),
# ]
#
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
