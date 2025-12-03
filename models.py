# ============================================================================
# models.py - Modèles de données
# Architecture : Chantier > Lot > Tâche > Heures/Photos
# ============================================================================

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Q, F
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# CHOIX (Enums)
# ============================================================================

class StatusChantier(models.TextChoices):
    """États possibles d'un chantier"""
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    EN_COURS = 'EN_COURS', 'En cours'
    EN_PAUSE = 'EN_PAUSE', 'En pause'
    TERMINE = 'TERMINE', 'Terminé'
    FACTURE = 'FACTURE', 'Facturé'
    ANNULE = 'ANNULE', 'Annulé'


class StatusTache(models.TextChoices):
    """États possibles d'une tâche"""
    A_FAIRE = 'A_FAIRE', 'À faire'
    EN_COURS = 'EN_COURS', 'En cours'
    EN_ATTENTE = 'EN_ATTENTE', 'En attente (bloqu é)'
    TERMINEE = 'TERMINEE', 'Terminée'
    REVISEE = 'REVISEE', 'Révisée'


class RoleMembre(models.TextChoices):
    """Rôles des membres d'équipe"""
    CHEF = 'CHEF', 'Chef de chantier'
    CHEF_EQUIPE = 'CHEF_EQUIPE', 'Chef d\'équipe'
    OUVRIER = 'OUVRIER', 'Ouvrier'
    APPRENTI = 'APPRENTI', 'Apprenti'
    AUTRE = 'AUTRE', 'Autre'


class TypeSousTraitant(models.TextChoices):
    """Types de spécialités des sous-traitants"""
    COUVERTURE = 'COUVERTURE', 'Couverture'
    PLOMBERIE = 'PLOMBERIE', 'Plomberie'
    ELECTRICITE = 'ELECTRICITE', 'Électricité'
    MENUISERIE = 'MENUISERIE', 'Menuiserie'
    PEINTURE = 'PEINTURE', 'Peinture'
    CARRELAGE = 'CARRELAGE', 'Carrelage'
    CLOISONS = 'CLOISONS', 'Cloisons/Isolation'
    MACONNERIE = 'MACONNERIE', 'Maçonnerie'
    EXCAVATION = 'EXCAVATION', 'Excavation/Terrassement'
    AUTRE = 'AUTRE', 'Autre'


# ============================================================================
# MODEL : CHANTIER (Projet principal)
# ============================================================================

class Chantier(models.Model):
    """
    Représente un chantier/projet complet.
    
    Exemples :
    - Rénovation d'une maison
    - Construction d'un bâtiment
    - Travaux de route
    """
    
    # Identifiants
    numero = models.CharField(
        max_length=50,
        unique=True,
        help_text="Numéro unique du chantier (ex: CH-2024-001)"
    )
    nom = models.CharField(max_length=200, help_text="Nom/description du chantier")
    
    # Localisation
    adresse = models.CharField(max_length=255, help_text="Adresse complète du chantier")
    codepostal = models.CharField(max_length=10)
    ville = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True, help_text="GPS latitude")
    longitude = models.FloatField(null=True, blank=True, help_text="GPS longitude")
    
    # Dates
    date_debut = models.DateField()
    date_fin_prevue = models.DateField()
    date_fin_reelle = models.DateField(null=True, blank=True)
    
    # Gestion
    status = models.CharField(
        max_length=20,
        choices=StatusChantier.choices,
        default=StatusChantier.EN_ATTENTE
    )
    chef = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='chantiers_diriges',
        help_text="Chef responsable du chantier"
    )
    
    # Budget
    budget_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    cout_reel = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Calculé automatiquement"
    )
    
    # Notes
    description = models.TextField(blank=True)
    notes_internes = models.TextField(blank=True, help_text="Notes non visibles au client")
    
    # Métadonnées
    creé_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='chantiers_crees'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['status']),
            models.Index(fields=['date_debut']),
        ]
        verbose_name_plural = 'Chantiers'
    
    def __str__(self):
        return f"{self.numero} - {self.nom}"
    
    def get_progression_percentage(self):
        """Calcule le % d'avancement du chantier"""
        lots = self.lots.all()
        if not lots.exists():
            return 0
        total_taches = sum(lot.taches.count() for lot in lots)
        if total_taches == 0:
            return 0
        taches_terminees = sum(
            lot.taches.filter(status=StatusTache.TERMINEE).count() 
            for lot in lots
        )
        return (taches_terminees / total_taches) * 100
    
    def calculer_cout_reel(self):
        """Recalcule le coût réel basé sur les heures travaillées"""
        total = Decimal('0')
        for lot in self.lots.all():
            for tache in lot.taches.all():
                total += tache.calculer_cout_heures()
        self.cout_reel = total
        self.save(update_fields=['cout_reel'])
        return total
    
    def jours_restants(self):
        """Nombre de jours avant la fin prévue"""
        delta = self.date_fin_prevue - timezone.now().date()
        return delta.days if delta.days >= 0 else 0


# ============================================================================
# MODEL : LOT (Phase du chantier)
# ============================================================================

class Lot(models.Model):
    """
    Représente une phase/lot d'un chantier.
    
    Exemple : Pour une rénovation :
    - Lot 1 : Démolition intérieure
    - Lot 2 : Gros oeuvre
    - Lot 3 : Second oeuvre
    """
    
    chantier = models.ForeignKey(
        Chantier,
        on_delete=models.CASCADE,
        related_name='lots',
        help_text="Chantier parent"
    )
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Ordonnancement
    numero = models.PositiveIntegerField(help_text="Numéro d'ordre (1, 2, 3...)")
    date_debut_prevue = models.DateField()
    date_fin_prevue = models.DateField()
    
    # Gestion
    responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lots_diriges'
    )
    
    # Budget par lot
    budget_lot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Budget alloué à ce lot"
    )
    
    # Statut
    status = models.CharField(
        max_length=20,
        choices=StatusChantier.choices,
        default=StatusChantier.EN_ATTENTE
    )
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['chantier', 'numero']
        unique_together = ['chantier', 'numero']
        verbose_name_plural = 'Lots'
    
    def __str__(self):
        return f"{self.chantier.numero} - Lot {self.numero}: {self.nom}"
    
    def get_progression_percentage(self):
        """% d'avancement du lot"""
        taches = self.taches.all()
        if not taches.exists():
            return 0
        terminees = taches.filter(status=StatusTache.TERMINEE).count()
        return (terminees / taches.count()) * 100


# ============================================================================
# MODEL : TÂCHE (Travail détaillé)
# ============================================================================

class Tache(models.Model):
    """
    Représente une tâche/travail détaillé.
    
    Exemple : Pour le lot "Gros oeuvre" :
    - Fondations
    - Armature béton
    - Coulage béton
    - etc.
    """
    
    # Identité
    lot = models.ForeignKey(
        Lot,
        on_delete=models.CASCADE,
        related_name='taches'
    )
    numero = models.CharField(max_length=50, help_text="Numéro de tâche (T-001, T-002...)")
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Ordonnancement
    ordre = models.PositiveIntegerField(default=0, help_text="Ordre d'exécution")
    date_debut_prevue = models.DateField()
    date_fin_prevue = models.DateField()
    date_debut_reelle = models.DateField(null=True, blank=True)
    date_fin_reelle = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=StatusTache.choices,
        default=StatusTache.A_FAIRE
    )
    
    # Ressources
    equipe = models.ForeignKey(
        'Equipe',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taches'
    )
    sous_traitants = models.ManyToManyField(
        'SousTraitant',
        blank=True,
        related_name='taches',
        help_text="Sous-traitants impliqués"
    )
    
    # Budget
    heures_estimees = models.DecimalField(
        max_digits=8,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('0'))]
    )
    heures_reelles = models.DecimalField(
        max_digits=8,
        decimal_places=1,
        default=0,
        editable=False,  # Calculé via HeureTravail
        help_text="Somme des heures enregistrées"
    )
    taux_horaire = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=50,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Taux horaire moyen de l'équipe"
    )
    
    # Notes
    notes = models.TextField(blank=True)
    bloquee_par = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='bloque',
        help_text="Tâches qui blocent celle-ci"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['lot', 'ordre']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['lot', 'status']),
        ]
    
    def __str__(self):
        return f"{self.numero} - {self.nom}"
    
    def calculer_cout_heures(self):
        """Calcule le coût total basé sur les heures réelles"""
        return self.heures_reelles * self.taux_horaire
    
    def calculer_heures_reelles(self):
        """Met à jour heures_reelles en sommant les entrées HeureTravail"""
        total = self.heures_travail.aggregate(Sum('heures'))['heures__sum'] or 0
        self.heures_reelles = Decimal(str(total))
        self.save(update_fields=['heures_reelles'])
        # Recalculer le coût du chantier parent
        self.lot.chantier.calculer_cout_reel()
        return self.heures_reelles
    
    def est_en_retard(self):
        """Vérifie si la tâche est en retard"""
        if self.status == StatusTache.TERMINEE:
            if self.date_fin_reelle and self.date_fin_reelle > self.date_fin_prevue:
                return True
        else:
            if timezone.now().date() > self.date_fin_prevue:
                return True
        return False


# ============================================================================
# MODEL : HEURE TRAVAIL (Suivi des heures)
# ============================================================================

class HeureTravail(models.Model):
    """
    Enregistrement des heures travaillées par un membre.
    
    C'est ici que les chefs de chantier enregistrent
    les heures réelles depuis le terrain.
    """
    
    tache = models.ForeignKey(
        Tache,
        on_delete=models.CASCADE,
        related_name='heures_travail'
    )
    membre = models.ForeignKey(
        'Membre',
        on_delete=models.SET_NULL,
        null=True,
        related_name='heures_travail'
    )
    date = models.DateField(default=timezone.now)
    heures = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('24'))]
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Travaux effectués (optionnel)"
    )
    
    # Géolocalisation
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Validation
    validee = models.BooleanField(default=False, help_text="Validée par le chef")
    validee_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='heures_validees'
    )
    
    date_enregistrement = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['tache', 'date']),
            models.Index(fields=['membre', 'date']),
        ]
    
    def __str__(self):
        return f"{self.tache.numero} - {self.membre} - {self.heures}h le {self.date}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mettre à jour le total des heures de la tâche
        self.tache.calculer_heures_reelles()
    
    def delete(self, *args, **kwargs):
        tache = self.tache
        super().delete(*args, **kwargs)
        # Mettre à jour après suppression
        tache.calculer_heures_reelles()


# ============================================================================
# MODEL : PHOTO RAPPORT (Suivi photographique)
# ============================================================================

class PhotoRapport(models.Model):
    """
    Photos de progression du chantier.
    
    Permet aux chefs de terrain de documenter
    l'avancement avec photos géolocalisées et commentaires.
    """
    
    tache = models.ForeignKey(
        Tache,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    titre = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    
    # Photo
    image = models.ImageField(
        upload_to='chantiers/photos/%Y/%m/%d/',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])
        ],
        help_text="Format : JPG, PNG, WebP. Max 5MB"
    )
    
    # Métadonnées photo
    latitude = models.FloatField(null=True, blank=True, help_text="GPS latitude")
    longitude = models.FloatField(null=True, blank=True, help_text="GPS longitude")
    date_photo = models.DateTimeField(default=timezone.now)
    
    # Validation
    approuvee = models.BooleanField(default=False)
    approuvee_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos_approuvees'
    )
    
    # Métadonnées
    uploadée_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='photos_uploadees'
    )
    date_upload = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_photo']
        indexes = [
            models.Index(fields=['tache', 'date_photo']),
        ]
    
    def __str__(self):
        return f"Photo - {self.tache.numero} - {self.date_photo.strftime('%d/%m/%Y')}"


# ============================================================================
# MODEL : ÉQUIPE (Groupes de travail)
# ============================================================================

class Equipe(models.Model):
    """
    Représente une équipe de travail interne.
    
    Exemple :
    - Équipe Maçonnerie
    - Équipe Plomberie
    - Équipe Électricité
    """
    
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Chef d'équipe
    chef = models.OneToOneField(
        'Membre',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipe_chef'
    )
    
    # Spécialité
    specialite = models.CharField(
        max_length=50,
        choices=TypeSousTraitant.choices,
        help_text="Domaine de compétence"
    )
    
    # Contrats
    contrat_externe = models.BooleanField(
        default=False,
        help_text="Équipe sous-contractée ?"
    )
    
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.specialite})"
    
    def get_membres_count(self):
        """Nombre de membres dans l'équipe"""
        return self.membres.filter(actif=True).count()


# ============================================================================
# MODEL : MEMBRE (Personne de l'équipe)
# ============================================================================

class Membre(models.Model):
    """
    Représente une personne membre d'une équipe.
    
    Peut être interne ou externe (sous-traitant).
    """
    
    # Identité
    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True)
    
    # Affectation
    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='membres'
    )
    role = models.CharField(
        max_length=20,
        choices=RoleMembre.choices,
        default=RoleMembre.OUVRIER
    )
    
    # Compétences
    qualifications = models.CharField(
        max_length=255,
        blank=True,
        help_text="Certifications, habilitations (virgule-séparé)"
    )
    
    # Gestion
    taux_horaire = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=50,
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    actif = models.BooleanField(default=True)
    date_embauche = models.DateField()
    
    # Métadonnées
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='membre_profil',
        help_text="Compte utilisateur Django (optionnel)"
    )
    
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['nom', 'prenom']
        indexes = [
            models.Index(fields=['equipe', 'actif']),
        ]
    
    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.role})"
    
    def get_heures_ce_mois(self):
        """Heures travaillées ce mois-ci"""
        from django.utils import timezone
        from dateutil.relativedelta import relativedelta
        
        debut_mois = timezone.now().replace(day=1)
        fin_mois = debut_mois + relativedelta(months=1) - relativedelta(days=1)
        
        total = self.heures_travail.filter(
            date__gte=debut_mois,
            date__lte=fin_mois
        ).aggregate(Sum('heures'))['heures__sum'] or 0
        
        return Decimal(str(total))


# ============================================================================
# MODEL : SOUS-TRAITANT (Prestataires externes)
# ============================================================================

class SousTraitant(models.Model):
    """
    Représente un sous-traitant/prestataire externe.
    
    Exemple :
    - Électricien Jean Dupont SARL
    - Plombier Pierre Martin
    """
    
    # Identité
    nom_entreprise = models.CharField(max_length=200)
    nom_contact = models.CharField(max_length=200, blank=True)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    
    # Adresse
    adresse = models.CharField(max_length=255, blank=True)
    codepostal = models.CharField(max_length=10, blank=True)
    ville = models.CharField(max_length=100, blank=True)
    
    # Domaine de compétence
    specialites = models.CharField(
        max_length=255,
        choices=[(choice, choice) for choice in TypeSousTraitant.choices],
        help_text="Domaine principal de compétence"
    )
    
    # Conditions commerciales
    taux_horaire = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    conditions_paiement = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ex: 30 jours, 50% acompte..."
    )
    
    # Gestion
    reference_client = models.CharField(
        max_length=50,
        blank=True,
        help_text="Numéro client/fournisseur interne"
    )
    actif = models.BooleanField(default=True)
    
    # Évaluation
    note_moyenne = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=5.0,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('5'))],
        help_text="Note moyenne de qualité (0-5)"
    )
    
    # Notes
    notes = models.TextField(blank=True, help_text="Notes internes")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['nom_entreprise']
        verbose_name_plural = 'Sous-traitants'
    
    def __str__(self):
        return f"{self.nom_entreprise} ({self.specialites})"


# ============================================================================
# MODEL : ANOMALIE / SIGNALEMENT (Problèmes détectés)
# ============================================================================

class Anomalie(models.Model):
    """
    Signalements de problèmes/anomalies sur le chantier.
    
    Exemple :
    - Malfaçon détectée
    - Retard important
    - Risque de sécurité
    """
    
    SEVERITE_CHOICES = [
        ('CRITIQUE', 'Critique (arrêt du chantier)'),
        ('MAJEURE', 'Majeure (impact important)'),
        ('MINEURE', 'Mineure (corrigible rapidement)'),
    ]
    
    tache = models.ForeignKey(
        Tache,
        on_delete=models.CASCADE,
        related_name='anomalies'
    )
    titre = models.CharField(max_length=255)
    description = models.TextField()
    severite = models.CharField(max_length=10, choices=SEVERITE_CHOICES)
    
    # Responsabilité
    signalee_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='anomalies_signalees'
    )
    responsable_correction = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='anomalies_a_corriger'
    )
    
    # Suivi
    statut = models.CharField(
        max_length=20,
        choices=[
            ('OUVERTE', 'Ouverte'),
            ('EN_COURS', 'En cours de correction'),
            ('FERMEE', 'Fermée'),
            ('REPORTEE', 'Reportée'),
        ],
        default='OUVERTE'
    )
    date_resolution_prevue = models.DateField(null=True, blank=True)
    date_resolution_reelle = models.DateField(null=True, blank=True)
    
    # Photo de référence
    photo = models.ForeignKey(
        PhotoRapport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='anomalies'
    )
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"[{self.severite}] {self.titre}"
    
    def est_en_retard(self):
        """Vérifie si la correction est en retard"""
        if self.statut != 'FERMEE' and self.date_resolution_prevue:
            return timezone.now().date() > self.date_resolution_prevue
        return False


# ============================================================================
# SIGNAUX DJANGO (Hooks automatiques)
# ============================================================================

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=HeureTravail)
def maj_heures_tache(sender, instance, **kwargs):
    """Signal : Mettre à jour heures_reelles quand on ajoute des heures"""
    instance.tache.calculer_heures_reelles()

@receiver(post_save, sender=Chantier)
def log_changement_chantier(sender, instance, created, **kwargs):
    """Signal : Logger les créations/modifications de chantier"""
    if created:
        logger.info(f"Chantier créé : {instance.numero} - {instance.nom}")
    else:
        logger.info(f"Chantier modifié : {instance.numero}")
