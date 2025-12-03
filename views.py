# ============================================================================
# views.py - API Endpoints (ViewSets + Permissions)
# Cœur de l'API REST consommée par le frontend/mobile
# ============================================================================

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q, Count, F
from django.utils import timezone
from django.shortcuts import get_object_or_404

import logging
from decimal import Decimal

from .models import (
    Chantier, Lot, Tache, HeureTravail, PhotoRapport,
    Equipe, Membre, SousTraitant, Anomalie
)
from .serializers import (
    ChantiersSerializer, ChantiersDetailSerializer,
    LotSerializer, TacheSerializer,
    HeuresTravailSerializer, PhotoRapportSerializer,
    EquipeSerializer, MembreSerializer,
    SousTraitantSerializer, AnomalieSerializer,
    RapportChantierSerializer
)
from .permissions import (
    IsChefOrReadOnly, IsMembreEquipe,
    IsChefChantier
)
from .filters import (
    ChantiersFilter, TacheFilter
)

logger = logging.getLogger(__name__)

# ============================================================================
# VIEWSET : CHANTIERS
# ============================================================================

class ChantiersViewSet(viewsets.ModelViewSet):
    """
    API complète pour les chantiers.
    
    Endpoints:
    - GET    /api/v1/chantiers/              → Lister (filtrable)
    - POST   /api/v1/chantiers/              → Créer
    - GET    /api/v1/chantiers/{id}/         → Détail
    - PATCH  /api/v1/chantiers/{id}/         → Mettre à jour
    - DELETE /api/v1/chantiers/{id}/         → Supprimer
    - GET    /api/v1/chantiers/{id}/rapport/ → Rapport complet
    """
    
    queryset = Chantier.objects.filter(actif=True).prefetch_related('lots__taches')
    serializer_class = ChantiersSerializer
    permission_classes = [IsAuthenticated, IsChefOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ChantiersFilter
    search_fields = ['numero', 'nom', 'adresse', 'ville']
    ordering_fields = ['date_creation', 'date_debut', 'status']
    ordering = ['-date_creation']
    
    def get_serializer_class(self):
        """Utiliser serializer détaillé pour retrieve"""
        if self.action == 'retrieve':
            return ChantiersDetailSerializer
        return super().get_serializer_class()
    
    def perform_create(self, serializer):
        """Ajouter l'utilisateur actuel comme créateur"""
        serializer.save(creé_par=self.request.user)
        logger.info(f"Chantier créé : {serializer.instance.numero} par {self.request.user}")
    
    @action(detail=True, methods=['get'])
    def rapport(self, request, pk=None):
        """
        Action personnalisée : Rapport d'avancement complet
        GET /api/v1/chantiers/{id}/rapport/
        """
        chantier = self.get_object()
        
        # Calculer les stats
        lots = chantier.lots.all()
        taches_totales = sum(lot.taches.count() for lot in lots)
        taches_terminees = sum(
            lot.taches.filter(status='TERMINEE').count() for lot in lots
        )
        
        heures_estimees = sum(
            lot.taches.aggregate(Sum('heures_estimees'))['heures_estimees__sum'] or 0
            for lot in lots
        )
        heures_reelles = sum(
            lot.taches.aggregate(Sum('heures_reelles'))['heures_reelles__sum'] or 0
            for lot in lots
        )
        
        progression = (taches_terminees / taches_totales * 100) if taches_totales else 0
        
        anomalies_ouvertes = Anomalie.objects.filter(
            tache__lot__chantier=chantier,
            statut__in=['OUVERTE', 'EN_COURS']
        ).count()
        
        membres_actifs = Membre.objects.filter(
            equipe__taches__lot__chantier=chantier,
            actif=True
        ).distinct().count()
        
        data = {
            'chantier': ChantiersSerializer(chantier).data,
            'lots': LotSerializer(lots, many=True).data,
            'taches_totales': taches_totales,
            'taches_terminees': taches_terminees,
            'progression_percentage': round(progression, 1),
            'heures_estimees': heures_estimees,
            'heures_reelles': heures_reelles,
            'cout_previsionnel': chantier.budget_total,
            'cout_reel': chantier.cout_reel,
            'anomalies_ouvertes': anomalies_ouvertes,
            'membres_actifs': membres_actifs,
        }
        
        return Response(data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def equipes(self, request, pk=None):
        """Lister les équipes affectées à ce chantier"""
        chantier = self.get_object()
        equipes = Equipe.objects.filter(
            taches__lot__chantier=chantier
        ).distinct()
        serializer = EquipeSerializer(equipes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def anomalies(self, request, pk=None):
        """Lister les anomalies du chantier"""
        chantier = self.get_object()
        anomalies = Anomalie.objects.filter(
            tache__lot__chantier=chantier
        ).order_by('-date_creation')
        
        # Filtrer par statut si fourni
        statut = request.query_params.get('statut')
        if statut:
            anomalies = anomalies.filter(statut=statut)
        
        serializer = AnomalieSerializer(anomalies, many=True)
        return Response(serializer.data)


# ============================================================================
# VIEWSET : LOTS
# ============================================================================

class LotsViewSet(viewsets.ModelViewSet):
    """
    Gestion des lots (phases) d'un chantier.
    Filtrable par chantier_id.
    """
    
    serializer_class = LotSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['chantier', 'status']
    ordering_fields = ['numero', 'date_debut_prevue']
    ordering = ['numero']
    
    def get_queryset(self):
        """Retourner les lots du chantier fourni"""
        chantier_id = self.request.query_params.get('chantier_id')
        if chantier_id:
            return Lot.objects.filter(chantier_id=chantier_id)
        return Lot.objects.all()


# ============================================================================
# VIEWSET : TÂCHES (Point central pour l'API mobile)
# ============================================================================

class TachesViewSet(viewsets.ModelViewSet):
    """
    Gestion des tâches - POINT CENTRAL POUR L'APP MOBILE.
    
    Endpoints clés :
    - GET    /api/v1/taches/                    → Lister (filtrable)
    - POST   /api/v1/taches/                    → Créer une tâche
    - GET    /api/v1/taches/{id}/               → Détail
    - PATCH  /api/v1/taches/{id}/               → Mettre à jour status, heures, etc.
    - POST   /api/v1/taches/{id}/photo/         → Ajouter une photo
    - GET    /api/v1/taches/{id}/heures/        → Historique des heures
    - POST   /api/v1/taches/{id}/heures/        → Enregistrer des heures (MOBILE)
    - GET    /api/v1/taches/{id}/anomalies/     → Anomalies de la tâche
    """
    
    serializer_class = TacheSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TacheFilter
    search_fields = ['numero', 'nom', 'description']
    ordering_fields = ['date_fin_prevue', 'status', 'date_debut_prevue']
    ordering = ['date_fin_prevue']
    
    def get_queryset(self):
        """Optimiser les requêtes avec select_related"""
        return Tache.objects.select_related(
            'lot__chantier', 'equipe'
        ).prefetch_related(
            'heures_travail', 'photos', 'anomalies', 'sous_traitants'
        )
    
    def perform_create(self, serializer):
        """Log création"""
        instance = serializer.save()
        logger.info(f"Tâche créée : {instance.numero}")
    
    @action(detail=True, methods=['post'], parser_classes=(MultiPartParser, FormParser))
    def photo(self, request, pk=None):
        """
        Ajouter une photo à une tâche (MOBILE).
        POST /api/v1/taches/{id}/photo/
        
        Données:
        {
            "image": <file>,
            "titre": "Photo avant",
            "description": "État avant les travaux",
            "latitude": 45.123456,
            "longitude": 5.123456
        }
        """
        tache = self.get_object()
        
        serializer = PhotoRapportSerializer(data=request.data)
        if serializer.is_valid():
            photo = serializer.save(
                tache=tache,
                uploadée_par=request.user
            )
            logger.info(f"Photo uploadée : {photo.id} pour tâche {tache.numero}")
            return Response(
                PhotoRapportSerializer(photo).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'post'])
    def heures(self, request, pk=None):
        """
        GET  : Historique des heures de la tâche
        POST : Enregistrer des heures (MOBILE - endpoint principal)
        """
        tache = self.get_object()
        
        if request.method == 'GET':
            heures = tache.heures_travail.all().order_by('-date')
            serializer = HeuresTravailSerializer(heures, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Créer une nouvelle entrée d'heures
            serializer = HeuresTravailSerializer(data=request.data)
            if serializer.is_valid():
                heures = serializer.save(tache=tache)
                logger.info(f"Heures enregistrées : {heures.heures}h pour {tache.numero}")
                return Response(
                    HeuresTravailSerializer(heures).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def photos(self, request, pk=None):
        """Lister les photos de la tâche"""
        tache = self.get_object()
        photos = tache.photos.all().order_by('-date_photo')
        serializer = PhotoRapportSerializer(photos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def anomalies(self, request, pk=None):
        """Lister les anomalies de la tâche"""
        tache = self.get_object()
        anomalies = tache.anomalies.all().order_by('-date_creation')
        serializer = AnomalieSerializer(anomalies, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def signaler_anomalie(self, request, pk=None):
        """
        Signaler une anomalie (MOBILE).
        POST /api/v1/taches/{id}/signaler_anomalie/
        """
        tache = self.get_object()
        
        serializer = AnomalieSerializer(data=request.data)
        if serializer.is_valid():
            anomalie = serializer.save(
                tache=tache,
                signalee_par=request.user
            )
            logger.warning(f"Anomalie signalée [{anomalie.severite}] : {anomalie.titre}")
            return Response(
                AnomalieSerializer(anomalie).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# VIEWSET : HEURES TRAVAIL
# ============================================================================

class HeuresTravailViewSet(viewsets.ModelViewSet):
    """
    Gestion centralisée des heures travaillées.
    Utilisé pour les rapports et validations.
    """
    
    serializer_class = HeuresTravailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tache', 'membre', 'date', 'validee']
    ordering_fields = ['-date']
    ordering = ['-date']
    
    def get_queryset(self):
        """Optimiser les requêtes"""
        return HeureTravail.objects.select_related(
            'tache', 'membre', 'validee_par'
        )
    
    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valider une entrée d'heures (Chef uniquement)"""
        heures = self.get_object()
        
        # Vérifier permission (chef du chantier)
        chef = heures.tache.lot.chantier.chef
        if request.user != chef and not request.user.is_staff:
            return Response(
                {'detail': 'Vous n\'avez pas les permissions.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        heures.validee = True
        heures.validee_par = request.user
        heures.save()
        logger.info(f"Heures validées : {heures.id}")
        
        return Response(
            HeuresTravailSerializer(heures).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def mes_heures(self, request):
        """Mes heures travaillées ce mois-ci"""
        membre = get_object_or_404(Membre, user=request.user)
        
        from dateutil.relativedelta import relativedelta
        debut_mois = timezone.now().replace(day=1)
        fin_mois = debut_mois + relativedelta(months=1) - relativedelta(days=1)
        
        heures = HeureTravail.objects.filter(
            membre=membre,
            date__gte=debut_mois,
            date__lte=fin_mois
        )
        
        serializer = HeuresTravailSerializer(heures, many=True)
        total = sum(h['heures'] for h in serializer.data if 'heures' in h)
        
        return Response({
            'heures': serializer.data,
            'total_heures': total,
            'mois': debut_mois.strftime('%B %Y')
        })


# ============================================================================
# VIEWSET : ÉQUIPES
# ============================================================================

class EquipesViewSet(viewsets.ModelViewSet):
    """Gestion des équipes de travail"""
    
    queryset = Equipe.objects.filter(actif=True).prefetch_related('membres')
    serializer_class = EquipeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nom', 'specialite']
    ordering_fields = ['nom']
    ordering = ['nom']


# ============================================================================
# VIEWSET : MEMBRES
# ============================================================================

class MembresViewSet(viewsets.ModelViewSet):
    """Gestion des membres d'équipe"""
    
    queryset = Membre.objects.filter(actif=True).select_related('equipe', 'user')
    serializer_class = MembreSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['equipe', 'role']
    search_fields = ['prenom', 'nom', 'email']
    ordering = ['nom', 'prenom']


# ============================================================================
# VIEWSET : SOUS-TRAITANTS
# ============================================================================

class SousTraitantsViewSet(viewsets.ModelViewSet):
    """Gestion des sous-traitants"""
    
    queryset = SousTraitant.objects.filter(actif=True)
    serializer_class = SousTraitantSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['specialites']
    search_fields = ['nom_entreprise', 'nom_contact', 'email']
    ordering = ['nom_entreprise']


# ============================================================================
# VIEWSET : ANOMALIES
# ============================================================================

class AnomaliesViewSet(viewsets.ModelViewSet):
    """Gestion des anomalies et signalements"""
    
    serializer_class = AnomalieSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tache__lot__chantier', 'statut', 'severite']
    ordering_fields = ['-date_creation']
    ordering = ['-date_creation']
    
    def get_queryset(self):
        return Anomalie.objects.select_related(
            'tache', 'signalee_par', 'responsable_correction'
        )
    
    @action(detail=True, methods=['post'])
    def assigner(self, request, pk=None):
        """Assigner une anomalie à quelqu'un pour correction"""
        anomalie = self.get_object()
        responsable_id = request.data.get('responsable_id')
        
        try:
            responsable = User.objects.get(id=responsable_id)
            anomalie.responsable_correction = responsable
            anomalie.statut = 'EN_COURS'
            anomalie.save()
            logger.info(f"Anomalie assignée : {anomalie.id} à {responsable}")
            return Response(
                AnomalieSerializer(anomalie).data,
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'detail': 'Utilisateur non trouvé.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def fermer(self, request, pk=None):
        """Fermer une anomalie"""
        anomalie = self.get_object()
        anomalie.statut = 'FERMEE'
        anomalie.date_resolution_reelle = timezone.now().date()
        anomalie.save()
        logger.info(f"Anomalie fermée : {anomalie.id}")
        return Response(
            AnomalieSerializer(anomalie).data,
            status=status.HTTP_200_OK
        )
