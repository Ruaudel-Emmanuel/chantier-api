# =================================================================
# permissions_filters.py - Permissions et filtres DRF
# Contrôle d'accès granulaire et filtrage avancé
# =================================================================

import django_filters
from django.utils import timezone
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Chantier, Membre, Tache, StatusChantier, StatusTache


# =================================================================
# PERMISSIONS PERSONNALISÉES
# =================================================================


class IsChefOrReadOnly(BasePermission):
    """
    Permission : Seul le chef du chantier (ou staff) peut modifier.
    Lecture possible pour tous les utilisateurs authentifiés.
    """

    message = "Vous devez être chef du chantier pour modifier."

    def has_object_permission(self, request, view, obj):
        # Lecture toujours autorisée pour authentifiés
        if request.method in SAFE_METHODS:
            return True

        # Modification réservée au chef ou staff
        return request.user == obj.chef or request.user.is_staff


class IsChefChantier(BasePermission):
    """Permission : Accès réservé au chef du chantier uniquement."""

    message = "Seul le chef du chantier peut accéder."

    def has_object_permission(self, request, view, obj):
        # Accès direct au chantier
        if isinstance(obj, Chantier):
            return request.user == obj.chef or request.user.is_staff

        # Pour les objets liés au chantier
        if hasattr(obj, 'chantier'):
            return (
                request.user == obj.chantier.chef or
                request.user.is_staff
            )

        if hasattr(obj, 'lot') and hasattr(obj.lot, 'chantier'):
            return (
                request.user == obj.lot.chantier.chef or
                request.user.is_staff
            )

        return False


class IsMembreEquipe(BasePermission):
    """Permission : L'utilisateur est membre de l'équipe."""

    message = "Vous n'êtes pas membre de cette équipe."

    def has_object_permission(self, request, view, obj):
        try:
            membre = Membre.objects.get(user=request.user)

            # Vérifier si le membre appartient à l'équipe
            if hasattr(obj, 'equipe'):
                return (
                    obj.equipe == membre.equipe or
                    request.user.is_staff
                )

            return False

        except Membre.DoesNotExist:
            return request.user.is_staff


class IsAuthenticated(BasePermission):
    """Permission : L'utilisateur doit être authentifié."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsAdminUser(BasePermission):
    """Permission : Réservé aux administrateurs."""

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


# =================================================================
# FILTRES PERSONNALISÉS
# =================================================================


class ChantiersFilter(django_filters.FilterSet):
    """
    Filtres avancés pour les chantiers.
    Utilisation:
    /api/v1/chantiers/?status=EN_COURS&date_debut_after=2024-01-01
    """

    # Filtres sur dates
    date_debut_after = django_filters.DateFilter(
        field_name='date_debut',
        lookup_expr='gte',
        label='Date de début (à partir de)'
    )

    date_debut_before = django_filters.DateFilter(
        field_name='date_debut',
        lookup_expr='lte',
        label='Date de début (jusqu\'à)'
    )

    date_fin_before = django_filters.DateFilter(
        field_name='date_fin_prevue',
        lookup_expr='lte',
        label='Date de fin prévue (jusqu\'à)'
    )

    # Filtres sur budget
    budget_min = django_filters.NumberFilter(
        field_name='budget_total',
        lookup_expr='gte'
    )

    budget_max = django_filters.NumberFilter(
        field_name='budget_total',
        lookup_expr='lte'
    )

    # Filtre ville
    ville = django_filters.CharFilter(
        field_name='ville',
        lookup_expr='icontains'
    )

    # Filtre status
    status = django_filters.ChoiceFilter(
        choices=StatusChantier.choices
    )

    # Chantiers en retard
    en_retard = django_filters.BooleanFilter(
        method='filter_en_retard'
    )

    def filter_en_retard(self, queryset, name, value):
        """Filtrer par chantiers en retard."""
        if value:
            today = timezone.now().date()
            return queryset.filter(
                date_fin_prevue__lt=today,
                status__in=['EN_COURS', 'EN_ATTENTE']
            )

        return queryset

    class Meta:
        model = Chantier
        fields = ['status', 'actif']


class TacheFilter(django_filters.FilterSet):
    """
    Filtres avancés pour les tâches.
    Utilisation:
    /api/v1/taches/?lot=1&status=EN_COURS&en_retard=true
    """

    # Par lot
    lot = django_filters.NumberFilter(
        field_name='lot__id'
    )

    # Par chantier (indirectement)
    chantier_id = django_filters.NumberFilter(
        field_name='lot__chantier__id'
    )

    # Par équipe
    equipe = django_filters.NumberFilter(
        field_name='equipe__id'
    )

    # Par status
    status = django_filters.ChoiceFilter(
        choices=StatusTache.choices
    )

    # Par date de fin
    date_fin_after = django_filters.DateFilter(
        field_name='date_fin_prevue',
        lookup_expr='gte'
    )

    date_fin_before = django_filters.DateFilter(
        field_name='date_fin_prevue',
        lookup_expr='lte'
    )

    # Tâches en retard
    en_retard = django_filters.BooleanFilter(
        method='filter_en_retard'
    )

    def filter_en_retard(self, queryset, name, value):
        """Filtrer par tâches en retard."""
        if value:
            today = timezone.now().date()
            return queryset.filter(
                date_fin_prevue__lt=today,
                status__in=['A_FAIRE', 'EN_COURS', 'EN_ATTENTE']
            )

        return queryset

    class Meta:
        model = Tache
        fields = ['status']
