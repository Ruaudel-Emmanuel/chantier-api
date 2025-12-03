# ============================================================================
# admin.py - Interface Django Admin personnalisée
# Pour gérer les données depuis /admin
# ============================================================================

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from .models import (
    Chantier, Lot, Tache, HeureTravail, PhotoRapport,
    Equipe, Membre, SousTraitant, Anomalie
)

# ============================================================================
# INLINE ADMINS - Pour les relations imbriquées
# ============================================================================

class LotInline(admin.TabularInline):
    """Éditer les lots directement depuis le chantier"""
    model = Lot
    extra = 1
    fields = ['numero', 'nom', 'date_debut_prevue', 'date_fin_prevue', 'budget_lot', 'status']


class TacheInline(admin.TabularInline):
    """Éditer les tâches directement depuis le lot"""
    model = Tache
    extra = 1
    fields = ['numero', 'nom', 'date_fin_prevue', 'status', 'heures_estimees']


class HeuresTravailInline(admin.TabularInline):
    """Historique des heures pour une tâche"""
    model = HeureTravail
    extra = 1
    fields = ['date', 'membre', 'heures', 'validee']
    can_delete = True


class PhotoRapportInline(admin.TabularInline):
    """Photos pour une tâche"""
    model = PhotoRapport
    extra = 1
    fields = ['titre', 'date_photo', 'approuvee']


class MembreInline(admin.TabularInline):
    """Membres d'une équipe"""
    model = Membre
    extra = 1
    fields = ['prenom', 'nom', 'role', 'taux_horaire', 'actif']


# ============================================================================
# ADMIN : CHANTIER
# ============================================================================

@admin.register(Chantier)
class ChantiersAdmin(admin.ModelAdmin):
    """Gestion complète des chantiers"""
    
    list_display = [
        'numero', 'nom', 'chef_display', 'status_display',
        'progression_display', 'budget_display', 'jours_restants_display'
    ]
    list_filter = ['status', 'date_creation', 'date_debut']
    search_fields = ['numero', 'nom', 'adresse', 'ville']
    readonly_fields = ['date_creation', 'date_modification', 'cout_reel', 'progression_display']
    
    fieldsets = (
        ('Identité', {
            'fields': ('numero', 'nom', 'description')
        }),
        ('Localisation', {
            'fields': ('adresse', 'codepostal', 'ville', 'latitude', 'longitude')
        }),
        ('Dates & Statut', {
            'fields': ('date_debut', 'date_fin_prevue', 'date_fin_reelle', 'status')
        }),
        ('Responsables', {
            'fields': ('chef', 'creé_par')
        }),
        ('Budget & Coûts', {
            'fields': ('budget_total', 'cout_reel', 'progression_display')
        }),
        ('Notes', {
            'fields': ('notes_internes',)
        }),
        ('Métadonnées', {
            'fields': ('actif', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [LotInline]
    
    def chef_display(self, obj):
        if obj.chef:
            return f"{obj.chef.first_name} {obj.chef.last_name}"
        return "-"
    chef_display.short_description = "Chef"
    
    def status_display(self, obj):
        colors = {
            'EN_ATTENTE': 'gray',
            'EN_COURS': 'blue',
            'EN_PAUSE': 'orange',
            'TERMINE': 'green',
            'FACTURE': 'purple',
            'ANNULE': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color:{}; color:white; padding:5px; border-radius:3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = "Statut"
    
    def progression_display(self, obj):
        progress = obj.get_progression_percentage()
        return format_html(
            '<div style="width:100px; height:20px; background-color:#f0f0f0; border-radius:10px;">'
            '<div style="width:{}%; height:100%; background-color:{}; border-radius:10px;"></div>'
            '</div>{}%',
            progress,
            'green' if progress == 100 else 'blue',
            int(progress)
        )
    progression_display.short_description = "Progression"
    
    def budget_display(self, obj):
        couleur = 'green' if obj.cout_reel <= obj.budget_total else 'red'
        return format_html(
            '<span style="color:{}; font-weight:bold;">{:.2f} / {:.2f} €</span>',
            couleur, obj.cout_reel, obj.budget_total
        )
    budget_display.short_description = "Budget (réel/total)"
    
    def jours_restants_display(self, obj):
        jours = obj.jours_restants()
        couleur = 'green' if jours > 7 else 'orange' if jours > 0 else 'red'
        return format_html(
            '<span style="color:{}; font-weight:bold;">{} j</span>',
            couleur, jours
        )
    jours_restants_display.short_description = "Jours restants"


# ============================================================================
# ADMIN : LOT
# ============================================================================

@admin.register(Lot)
class LotsAdmin(admin.ModelAdmin):
    """Gestion des lots"""
    
    list_display = ['numero', 'nom', 'chantier', 'status', 'date_fin_prevue']
    list_filter = ['status', 'chantier', 'date_fin_prevue']
    search_fields = ['nom', 'chantier__nom']
    
    inlines = [TacheInline]
    
    fieldsets = (
        ('Identité', {
            'fields': ('chantier', 'numero', 'nom', 'description')
        }),
        ('Dates', {
            'fields': ('date_debut_prevue', 'date_fin_prevue')
        }),
        ('Gestion', {
            'fields': ('responsable', 'budget_lot', 'status')
        })
    )


# ============================================================================
# ADMIN : TÂCHE
# ============================================================================

@admin.register(Tache)
class TachesAdmin(admin.ModelAdmin):
    """Gestion des tâches"""
    
    list_display = [
        'numero', 'nom', 'lot', 'status_badge',
        'heures_display', 'retard_badge'
    ]
    list_filter = ['status', 'lot__chantier', 'date_fin_prevue']
    search_fields = ['numero', 'nom', 'lot__nom']
    readonly_fields = ['heures_reelles', 'date_creation', 'date_modification']
    
    inlines = [HeuresTravailInline, PhotoRapportInline]
    
    fieldsets = (
        ('Identité', {
            'fields': ('lot', 'numero', 'nom', 'description')
        }),
        ('Calendrier', {
            'fields': ('ordre', 'date_debut_prevue', 'date_fin_prevue', 'date_debut_reelle', 'date_fin_reelle')
        }),
        ('Heures', {
            'fields': ('heures_estimees', 'heures_reelles', 'taux_horaire')
        }),
        ('Ressources', {
            'fields': ('equipe', 'sous_traitants', 'status')
        }),
        ('Blocages', {
            'fields': ('bloquee_par',),
            'classes': ('collapse',)
        })
    )
    
    def status_badge(self, obj):
        colors = {
            'A_FAIRE': 'gray',
            'EN_COURS': 'blue',
            'EN_ATTENTE': 'orange',
            'TERMINEE': 'green',
            'REVISEE': 'purple'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px; font-weight:bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Statut"
    
    def heures_display(self, obj):
        return f"{obj.heures_reelles}/{obj.heures_estimees}h"
    heures_display.short_description = "Heures"
    
    def retard_badge(self, obj):
        if obj.est_en_retard():
            return format_html(
                '<span style="background-color:red; color:white; padding:3px 8px; border-radius:3px; font-weight:bold;">⚠️ RETARD</span>'
            )
        return "-"
    retard_badge.short_description = "Retard"


# ============================================================================
# ADMIN : HEURES TRAVAIL
# ============================================================================

@admin.register(HeureTravail)
class HeuresTravailAdmin(admin.ModelAdmin):
    """Gestion des heures travaillées"""
    
    list_display = ['date', 'tache', 'membre', 'heures', 'validee_badge']
    list_filter = ['validee', 'date', 'tache__lot__chantier']
    search_fields = ['tache__numero', 'membre__nom']
    
    actions = ['marquer_validee', 'marquer_non_validee']
    
    def validee_badge(self, obj):
        if obj.validee:
            return format_html('<span style="color:green; font-weight:bold;">✓ Validée</span>')
        return format_html('<span style="color:orange; font-weight:bold;">⏳ En attente</span>')
    validee_badge.short_description = "Validation"
    
    @admin.action(description="Marquer comme validée")
    def marquer_validee(self, request, queryset):
        updated = queryset.update(validee=True, validee_par=request.user)
        self.message_user(request, f"{updated} entrée(s) validée(s).")
    
    @admin.action(description="Marquer comme non validée")
    def marquer_non_validee(self, request, queryset):
        updated = queryset.update(validee=False, validee_par=None)
        self.message_user(request, f"{updated} entrée(s) marquée(s) comme non validée(s).")


# ============================================================================
# ADMIN : ÉQUIPE
# ============================================================================

@admin.register(Equipe)
class EquipesAdmin(admin.ModelAdmin):
    """Gestion des équipes"""
    
    list_display = ['nom', 'specialite', 'chef', 'nombre_membres', 'actif']
    list_filter = ['specialite', 'actif']
    search_fields = ['nom']
    
    inlines = [MembreInline]
    
    def nombre_membres(self, obj):
        return obj.get_membres_count()
    nombre_membres.short_description = "Membres"


# ============================================================================
# ADMIN : MEMBRE
# ============================================================================

@admin.register(Membre)
class MembresAdmin(admin.ModelAdmin):
    """Gestion des membres"""
    
    list_display = ['prenom', 'nom', 'equipe', 'role', 'taux_horaire', 'actif']
    list_filter = ['equipe', 'role', 'actif']
    search_fields = ['prenom', 'nom', 'email']


# ============================================================================
# ADMIN : SOUS-TRAITANT
# ============================================================================

@admin.register(SousTraitant)
class SousTraitantsAdmin(admin.ModelAdmin):
    """Gestion des sous-traitants"""
    
    list_display = ['nom_entreprise', 'specialites', 'email', 'note_moyenne_display', 'actif']
    list_filter = ['specialites', 'actif']
    search_fields = ['nom_entreprise', 'nom_contact', 'email']
    
    def note_moyenne_display(self, obj):
        return format_html(
            '<span style="font-weight:bold; color:{};">⭐ {}/5</span>',
            'green' if obj.note_moyenne >= 4 else 'orange',
            obj.note_moyenne
        )
    note_moyenne_display.short_description = "Note"


# ============================================================================
# ADMIN : ANOMALIE
# ============================================================================

@admin.register(Anomalie)
class AnomaliesAdmin(admin.ModelAdmin):
    """Gestion des anomalies"""
    
    list_display = [
        'titre', 'tache', 'severite_badge', 'statut_badge',
        'signalee_par', 'date_creation'
    ]
    list_filter = ['severite', 'statut', 'date_creation']
    search_fields = ['titre', 'tache__numero']
    
    actions = ['marquer_ouverte', 'marquer_fermee']
    
    def severite_badge(self, obj):
        colors = {
            'CRITIQUE': 'red',
            'MAJEURE': 'orange',
            'MINEURE': 'yellow'
        }
        color = colors.get(obj.severite, 'gray')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px; font-weight:bold;">{}</span>',
            color, obj.get_severite_display()
        )
    severite_badge.short_description = "Sévérité"
    
    def statut_badge(self, obj):
        colors = {
            'OUVERTE': 'red',
            'EN_COURS': 'orange',
            'FERMEE': 'green',
            'REPORTEE': 'gray'
        }
        color = colors.get(obj.statut, 'gray')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            color, obj.get_statut_display()
        )
    statut_badge.short_description = "Statut"
    
    @admin.action(description="Marquer comme ouverte")
    def marquer_ouverte(self, request, queryset):
        queryset.update(statut='OUVERTE')
        self.message_user(request, "Anomalies marquées comme ouvertes.")
    
    @admin.action(description="Marquer comme fermée")
    def marquer_fermee(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            statut='FERMEE',
            date_resolution_reelle=timezone.now().date()
        )
        self.message_user(request, "Anomalies fermées.")


# ============================================================================
# ADMIN SITE CUSTOMIZATION
# ============================================================================

admin.site.site_header = "Gestion des Chantiers - Administration"
admin.site.site_title = "API Chantiers Admin"
admin.site.index_title = "Bienvenue dans le panel d'administration"
