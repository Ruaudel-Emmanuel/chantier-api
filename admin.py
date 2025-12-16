# ============================================================================
# admin.py - Interface Django Admin personnalisée
# Pour gérer les données depuis /admin
# ============================================================================

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Chantier,
    Lot,
    Tache,
    HeureTravail,
    PhotoRapport,
    Equipe,
    Membre,
    SousTraitant,
    Anomalie,
)

# ============================================================================
# INLINE ADMINS - Pour les relations imbriquées
# ============================================================================


class LotInline(admin.TabularInline):
    """Éditer les lots directement depuis le chantier."""

    model = Lot
    extra = 1
    fields = [
        "numero",
        "nom",
        "date_debut_prevue",
        "date_fin_prevue",
        "budget_lot",
        "status",
    ]


class TacheInline(admin.TabularInline):
    """Éditer les tâches directement depuis le lot."""

    model = Tache
    extra = 1
    fields = ["numero", "nom", "date_fin_prevue", "status", "heures_estimees"]


class HeuresTravailInline(admin.TabularInline):
    """Historique des heures pour une tâche."""

    model = HeureTravail
    extra = 1
    fields = ["date", "membre", "heures", "validee"]
    can_delete = True


class PhotoRapportInline(admin.TabularInline):
    """Photos pour une tâche."""

    model = PhotoRapport
    extra = 1
    fields = ["titre", "date_photo", "approuvee"]


class MembreInline(admin.TabularInline):
    """Membres d'une équipe."""

    model = Membre
    extra = 1
    fields = ["prenom", "nom", "role", "taux_horaire", "actif"]


# ============================================================================
# ADMIN : CHANTIER
# ============================================================================


@admin.register(Chantier)
class ChantiersAdmin(admin.ModelAdmin):
    """Gestion complète des chantiers."""

    list_display = [
        "numero",
        "nom",
        "chef_display",
        "status_display",
        "progression_display",
        "budget_display",
        "jours_restants_display",
    ]
    list_filter = ["status", "date_creation", "date_debut"]
    search_fields = ["numero", "nom", "adresse", "ville"]
    readonly_fields = [
        "date_creation",
        "date_modification",
        "cout_reel",
        "progression_display",
    ]
    fieldsets = (
        (
            "Identité",
            {
                "fields": ("numero", "nom", "description"),
            },
        ),
        (
            "Localisation",
            {
                "fields": (
                    "adresse",
                    "codepostal",
                    "ville",
                    "latitude",
                    "longitude",
                ),
            },
        ),
        (
            "Dates & Statut",
            {
                "fields": (
                    "date_debut",
                    "date_fin_prevue",
                    "date_fin_reelle",
                    "status",
                ),
            },
        ),
        (
            "Responsables",
            {
                "fields": ("chef", "creé_par"),
            },
        ),
        (
            "Budget & Coûts",
            {
                "fields": ("budget_total", "cout_reel", "progression_display"),
            },
        ),
        (
            "Notes",
            {
                "fields": ("notes_internes",),
            },
        ),
        (
            "Métadonnées",
            {
                "fields": ("actif", "date_creation", "date_modification"),
                "classes": ("collapse",),
            },
        ),
    )
    inlines = [LotInline]

    def chef_display(self, obj):
        if obj.chef:
            return f"{obj.chef.first_name} {obj.chef.last_name}"
        return "-"

    chef_display.short_description = "Chef"

    def status_display(self, obj):
        colors = {
            "EN_ATTENTE": "gray",
            "EN_COURS": "blue",
            "EN_PAUSE": "orange",
            "TERMINE": "green",
            "FACTURE": "purple",
            "ANNULE": "red",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_display.short_description = "Statut"

    def progression_display(self, obj):
        progress = obj.get_progression_percentage()
        return format_html(
            '<div style="width: 100px; border: 1px solid #ccc;">'
            '<div style="width: {}%; background-color: #4CAF50; '
            'height: 12px;"></div>'
            "</div> {}%",
            int(progress),
            int(progress),
        )

    progression_display.short_description = "Progression"

    def budget_display(self, obj):
        return f"{obj.cout_reel} / {obj.budget_total} €"

    budget_display.short_description = "Coût / Budget"

    def jours_restants_display(self, obj):
        jours = obj.get_jours_restants()
        if jours is None:
            return "-"
        if jours < 0:
            return format_html('<span style="color: red;">{} j</span>', jours)
        return f"{jours} j"

    jours_restants_display.short_description = "Jours restants"


# ============================================================================
# ADMIN : LOT
# ============================================================================


@admin.register(Lot)
class LotsAdmin(admin.ModelAdmin):
    """Gestion des lots."""

    list_display = [
        "numero",
        "nom",
        "chantier",
        "date_debut_prevue",
        "date_fin_prevue",
        "status",
    ]
    search_fields = [
        "titre",
        "tache__nom",
        "tache__lot__chantier__nom",
    ]

    search_fields = ["numero", "nom", "chantier__nom"]
    inlines = [TacheInline]


# ============================================================================
# ADMIN : TÂCHE
# ============================================================================


@admin.register(Tache)
class TachesAdmin(admin.ModelAdmin):
    """Gestion des tâches."""

    list_display = [
        "numero",
        "nom",
        "lot",
        "equipe",
        "status",
        "date_fin_prevue",
        "heures_estimees",
        "heures_reelles",
    ]
    list_filter = [
        "status",
        "date_fin_prevue",
        "lot__chantier",
        "equipe",
    ]
    search_fields = ["numero", "nom", "lot__chantier__nom"]
    inlines = [HeuresTravailInline, PhotoRapportInline]


# ============================================================================
# ADMIN : HEURES DE TRAVAIL
# ============================================================================


@admin.register(HeureTravail)
class HeuresTravailAdmin(admin.ModelAdmin):
    """Suivi des heures de travail."""

    list_display = [
        "date",
        "tache",
        "membre",
        "heures",
        "validee",
    ]
    list_filter = ["validee", "date", "membre", "tache__lot__chantier"]
    search_fields = ["tache__numero", "membre__nom", "membre__prenom"]


# ============================================================================
# ADMIN : ÉQUIPES & MEMBRES
# ============================================================================


@admin.register(Equipe)
class EquipesAdmin(admin.ModelAdmin):
    """Gestion des équipes."""

    list_display = ["nom", "chantier", "chef_equipe", "actif"]
    list_filter = ["actif", "chantier"]
    search_fields = ["nom", "chantier__nom"]
    inlines = [MembreInline]


@admin.register(Membre)
class MembresAdmin(admin.ModelAdmin):
    """Gestion des membres d'équipe."""

    list_display = [
        "prenom",
        "nom",
        "equipe",
        "role",
        "taux_horaire",
        "actif",
    ]
    list_filter = ["actif", "role", "equipe__chantier"]
    search_fields = ["prenom", "nom", "equipe__nom"]


# ============================================================================
# ADMIN : SOUS-TRAITANTS
# ============================================================================


@admin.register(SousTraitant)
class SousTraitantsAdmin(admin.ModelAdmin):
    """Gestion des sous-traitants."""

    list_display = [
        "nom_entreprise",
        "nom_contact",
        "specialites",
        "telephone",
        "actif",
    ]
    list_filter = ["actif", "specialites"]
    search_fields = [
        "nom_entreprise",
        "nom_contact",
        "ville",
        "specialites",
    ]


# ============================================================================
# ADMIN : ANOMALIES
# ============================================================================


@admin.register(Anomalie)
class AnomaliesAdmin(admin.ModelAdmin):
    """Gestion des anomalies / signalements."""

    list_display = [
        "titre",
        "tache",
        "severite",
        "statut",
        "signalee_par",
        "date_creation",
        "date_resolution_prevue",
    ]
    list_filter = [
        "severite",
        "statut",
        "date_creation",
        "date_resolution_prevue",
    ]
    search_fields = [
        "titre",
        "tache__nom",
        "tache__lot__chantier__nom",
    ]
