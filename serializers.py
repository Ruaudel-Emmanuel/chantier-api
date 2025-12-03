# ============================================================================
# serializers.py - Convertit les modèles en JSON
# Validation des données entrantes/sortantes
# ============================================================================

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import User
from .models import (
    Chantier, Lot, Tache, HeureTravail, PhotoRapport,
    Equipe, Membre, SousTraitant, Anomalie,
    StatusChantier, StatusTache, RoleMembre
)
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# NESTED SERIALIZERS (Objets imbriqués)
# ============================================================================

class UserSerializer(serializers.ModelSerializer):
    """Données utilisateur minimales"""
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']


class MembreBasicSerializer(serializers.ModelSerializer):
    """Infos basiques d'un membre"""
    class Meta:
        model = Membre
        fields = ['id', 'prenom', 'nom', 'email', 'role', 'taux_horaire']


# ============================================================================
# SERIALIZER : CHANTIER
# ============================================================================

class ChantiersSerializer(serializers.ModelSerializer):
    """
    Sérializer principal pour Chantier.
    Lecture/écriture complète avec validation métier.
    """
    
    # Champs imbriqués en lecture
    chef_detail = UserSerializer(source='chef', read_only=True)
    progression = serializers.SerializerMethodField()
    cout_reel = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    jours_restants = serializers.SerializerMethodField()
    nombre_taches = serializers.SerializerMethodField()
    
    class Meta:
        model = Chantier
        fields = [
            'id', 'numero', 'nom', 'description', 'adresse', 'codepostal',
            'ville', 'latitude', 'longitude',
            'date_debut', 'date_fin_prevue', 'date_fin_reelle',
            'status', 'chef', 'chef_detail',
            'budget_total', 'cout_reel',
            'progression', 'jours_restants', 'nombre_taches',
            'notes_internes', 'date_creation', 'actif'
        ]
        read_only_fields = ['date_creation', 'creé_par', 'cout_reel']
    
    def validate_numero(self, value):
        """Valide unicité du numéro"""
        if Chantier.objects.filter(numero=value).exists():
            raise serializers.ValidationError("Ce numéro existe déjà.")
        return value
    
    def validate(self, data):
        """Validations cross-fields"""
        if data['date_debut'] >= data['date_fin_prevue']:
            raise serializers.ValidationError(
                "La date de fin doit être après la date de début."
            )
        if data['budget_total'] <= 0:
            raise serializers.ValidationError(
                "Le budget doit être positif."
            )
        return data
    
    def get_progression(self, obj):
        """% d'avancement"""
        return round(obj.get_progression_percentage(), 1)
    
    def get_jours_restants(self, obj):
        """Jours avant fin"""
        return obj.jours_restants()
    
    def get_nombre_taches(self, obj):
        """Nombre total de tâches"""
        return sum(lot.taches.count() for lot in obj.lots.all())


class ChantiersDetailSerializer(ChantiersSerializer):
    """Version détaillée avec lots imbriqués"""
    lots = serializers.SerializerMethodField()
    
    class Meta(ChantiersSerializer.Meta):
        pass
    
    def get_lots(self, obj):
        """Inclure les lots du chantier"""
        lots = obj.lots.all()
        return LotSerializer(lots, many=True, context=self.context).data


# ============================================================================
# SERIALIZER : LOT
# ============================================================================

class LotSerializer(serializers.ModelSerializer):
    """Lot de chantier avec tâches imbriquées"""
    
    progression = serializers.SerializerMethodField()
    nombre_taches = serializers.SerializerMethodField()
    responsable_detail = UserSerializer(source='responsable', read_only=True)
    
    class Meta:
        model = Lot
        fields = [
            'id', 'chantier', 'numero', 'nom', 'description',
            'date_debut_prevue', 'date_fin_prevue',
            'responsable', 'responsable_detail',
            'budget_lot', 'status',
            'progression', 'nombre_taches',
            'date_creation'
        ]
        read_only_fields = ['date_creation']
    
    def get_progression(self, obj):
        return round(obj.get_progression_percentage(), 1)
    
    def get_nombre_taches(self, obj):
        return obj.taches.count()


# ============================================================================
# SERIALIZER : TÂCHE
# ============================================================================

class TacheSerializer(serializers.ModelSerializer):
    """
    Tâche complète avec relations.
    Utilisé par l'API mobile pour suivi terrain.
    """
    
    # Champs imbriqués
    equipe_detail = serializers.SerializerMethodField()
    heures_travail_count = serializers.SerializerMethodField()
    cout_total = serializers.SerializerMethodField()
    en_retard = serializers.SerializerMethodField()
    photos_count = serializers.SerializerMethodField()
    anomalies = serializers.SerializerMethodField()
    
    class Meta:
        model = Tache
        fields = [
            'id', 'lot', 'numero', 'nom', 'description',
            'ordre', 'date_debut_prevue', 'date_fin_prevue',
            'date_debut_reelle', 'date_fin_reelle',
            'status', 'heures_estimees', 'heures_reelles',
            'taux_horaire', 'cout_total',
            'equipe', 'equipe_detail', 'sous_traitants',
            'notes', 'en_retard',
            'heures_travail_count', 'photos_count', 'anomalies',
            'date_creation'
        ]
        read_only_fields = [
            'date_creation', 'heures_reelles', 'cout_total'
        ]
    
    def get_equipe_detail(self, obj):
        if obj.equipe:
            return {
                'id': obj.equipe.id,
                'nom': obj.equipe.nom,
                'specialite': obj.equipe.specialite,
                'chef': str(obj.equipe.chef) if obj.equipe.chef else None,
            }
        return None
    
    def get_heures_travail_count(self, obj):
        return obj.heures_travail.count()
    
    def get_cout_total(self, obj):
        return str(obj.calculer_cout_heures())
    
    def get_en_retard(self, obj):
        return obj.est_en_retard()
    
    def get_photos_count(self, obj):
        return obj.photos.count()
    
    def get_anomalies(self, obj):
        anomalies = obj.anomalies.filter(statut__in=['OUVERTE', 'EN_COURS'])
        return AnomalieSerializer(anomalies, many=True).data


# ============================================================================
# SERIALIZER : HEURE TRAVAIL (pour l'API mobile)
# ============================================================================

class HeuresTravailSerializer(serializers.ModelSerializer):
    """Enregistrement des heures (point d'entrée principal pour mobile)"""
    
    tache_detail = TacheSerializer(source='tache', read_only=True)
    membre_detail = MembreBasicSerializer(source='membre', read_only=True)
    validee_par_detail = UserSerializer(source='validee_par', read_only=True)
    
    class Meta:
        model = HeureTravail
        fields = [
            'id', 'tache', 'tache_detail',
            'membre', 'membre_detail',
            'date', 'heures', 'description',
            'latitude', 'longitude',
            'validee', 'validee_par', 'validee_par_detail',
            'date_enregistrement'
        ]
        read_only_fields = [
            'date_enregistrement', 'validee_par'
        ]
    
    def validate_heures(self, value):
        """Valide que les heures sont positives et ≤ 24"""
        if value <= 0:
            raise serializers.ValidationError("Les heures doivent être positives.")
        if value > 24:
            raise serializers.ValidationError("Impossible de travailler plus de 24h par jour.")
        return value


# ============================================================================
# SERIALIZER : PHOTO RAPPORT
# ============================================================================

class PhotoRapportSerializer(serializers.ModelSerializer):
    """Upload et gestion des photos terrain"""
    
    uploadée_par_detail = UserSerializer(source='uploadée_par', read_only=True)
    approuvee_par_detail = UserSerializer(source='approuvee_par', read_only=True)
    
    class Meta:
        model = PhotoRapport
        fields = [
            'id', 'tache', 'titre', 'description',
            'image', 'latitude', 'longitude',
            'date_photo', 'approuvee', 'approuvee_par',
            'approuvee_par_detail',
            'uploadée_par', 'uploadée_par_detail',
            'date_upload'
        ]
        read_only_fields = [
            'date_upload', 'uploadée_par', 'approuvee_par'
        ]
    
    def validate_image(self, value):
        """Valide taille et format de l'image"""
        if value.size > 5 * 1024 * 1024:  # 5 MB
            raise serializers.ValidationError("L'image dépasse 5 MB.")
        return value


# ============================================================================
# SERIALIZER : ÉQUIPE
# ============================================================================

class EquipeSerializer(serializers.ModelSerializer):
    """Équipes de travail"""
    
    chef_detail = MembreBasicSerializer(source='chef', read_only=True)
    nombre_membres = serializers.SerializerMethodField()
    
    class Meta:
        model = Equipe
        fields = [
            'id', 'nom', 'description', 'specialite',
            'chef', 'chef_detail',
            'contrat_externe', 'actif',
            'nombre_membres', 'date_creation'
        ]
        read_only_fields = ['date_creation']
    
    def get_nombre_membres(self, obj):
        return obj.get_membres_count()


# ============================================================================
# SERIALIZER : MEMBRE
# ============================================================================

class MembreSerializer(serializers.ModelSerializer):
    """Profil complet d'un membre"""
    
    equipe_detail = EquipeSerializer(source='equipe', read_only=True)
    heures_ce_mois = serializers.SerializerMethodField()
    
    class Meta:
        model = Membre
        fields = [
            'id', 'prenom', 'nom', 'email', 'telephone',
            'equipe', 'equipe_detail', 'role',
            'qualifications', 'taux_horaire',
            'date_embauche', 'actif',
            'heures_ce_mois',
            'date_creation'
        ]
        read_only_fields = ['date_creation']
    
    def get_heures_ce_mois(self, obj):
        return float(obj.get_heures_ce_mois())


# ============================================================================
# SERIALIZER : SOUS-TRAITANT
# ============================================================================

class SousTraitantSerializer(serializers.ModelSerializer):
    """Gestion des prestataires externes"""
    
    class Meta:
        model = SousTraitant
        fields = [
            'id', 'nom_entreprise', 'nom_contact', 'email', 'telephone',
            'adresse', 'codepostal', 'ville',
            'specialites', 'taux_horaire',
            'conditions_paiement', 'reference_client',
            'note_moyenne', 'actif', 'notes',
            'date_creation'
        ]
        read_only_fields = ['date_creation', 'note_moyenne']


# ============================================================================
# SERIALIZER : ANOMALIE
# ============================================================================

class AnomalieSerializer(serializers.ModelSerializer):
    """Signalements et anomalies"""
    
    signalee_par_detail = UserSerializer(source='signalee_par', read_only=True)
    responsable_detail = UserSerializer(source='responsable_correction', read_only=True)
    en_retard = serializers.SerializerMethodField()
    
    class Meta:
        model = Anomalie
        fields = [
            'id', 'tache', 'titre', 'description', 'severite', 'statut',
            'signalee_par', 'signalee_par_detail',
            'responsable_correction', 'responsable_detail',
            'date_resolution_prevue', 'date_resolution_reelle',
            'photo', 'en_retard',
            'date_creation', 'date_modification'
        ]
        read_only_fields = [
            'date_creation', 'date_modification', 'signalee_par'
        ]
    
    def get_en_retard(self, obj):
        return obj.est_en_retard()


# ============================================================================
# SERIALIZERS COMBINÉS (Pour endpoints complexes)
# ============================================================================

class RapportChantierSerializer(serializers.Serializer):
    """Rapport d'avancement complet du chantier"""
    chantier = ChantiersSerializer()
    lots = LotSerializer(many=True)
    taches_totales = serializers.IntegerField()
    taches_terminees = serializers.IntegerField()
    progression_percentage = serializers.FloatField()
    heures_estimees = serializers.DecimalField(max_digits=10, decimal_places=1)
    heures_reelles = serializers.DecimalField(max_digits=10, decimal_places=1)
    cout_previsionnel = serializers.DecimalField(max_digits=12, decimal_places=2)
    cout_reel = serializers.DecimalField(max_digits=12, decimal_places=2)
    anomalies_ouvertes = serializers.IntegerField()
    membres_actifs = serializers.IntegerField()
