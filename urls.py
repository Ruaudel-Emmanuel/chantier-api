# =================================================================
# urls.py - Configuration des routes URL principales
# Routage API + Admin + Documentation Swagger
# =================================================================

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from chantiers.views import (
    AnomaliesViewSet,
    ChantiersViewSet,
    EquipesViewSet,
    HeuresTravailViewSet,
    LotsViewSet,
    MembresViewSet,
    SousTraitantsViewSet,
    TachesViewSet
)

# =================================================================
# CONFIGURATION DU ROUTEUR DRF
# =================================================================

router = DefaultRouter()
router.register(r'chantiers', ChantiersViewSet, basename='chantier')
router.register(r'lots', LotsViewSet, basename='lot')
router.register(r'taches', TachesViewSet, basename='tache')
router.register(
    r'heures',
    HeuresTravailViewSet,
    basename='heuretravail'
)
router.register(r'equipes', EquipesViewSet, basename='equipe')
router.register(r'membres', MembresViewSet, basename='membre')
router.register(
    r'soustraitants',
    SousTraitantsViewSet,
    basename='soustraitant'
)
router.register(r'anomalies', AnomaliesViewSet, basename='anomalie')

# =================================================================
# PATTERNS URL
# =================================================================

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),

    # API REST
    path('api/v1/', include(router.urls)),

    # Auth DRF (login/logout pour Browsable API)
    path('api-auth/', include('rest_framework.urls')),
]

# =================================================================
# DOCUMENTATION API (Swagger/ReDoc)
# =================================================================

if settings.DEBUG:
    from drf_yasg import openapi
    from drf_yasg.views import get_schema_view
    from rest_framework import permissions

    schema_view = get_schema_view(
        openapi.Info(
            title="Chantiers API",
            default_version='v1',
            description=(
                "API REST pour gestion de chantiers BTP - "
                "Suivi tâches, heures, équipes, anomalies"
            ),
            terms_of_service="https://www.example.com/terms/",
            contact=openapi.Contact(email="contact@chantiers.local"),
            license=openapi.License(name="MIT License"),
        ),
        public=True,
        permission_classes=[permissions.AllowAny],
    )

    urlpatterns += [
        path(
            'swagger/',
            schema_view.with_ui('swagger', cache_timeout=0),
            name='schema-swagger-ui'
        ),
        path(
            'redoc/',
            schema_view.with_ui('redoc', cache_timeout=0),
            name='schema-redoc'
        ),
    ]

# =================================================================
# FICHIERS MEDIA (en développement uniquement)
# =================================================================

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
