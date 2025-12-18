# =================================================================
# tests.py - Tests unitaires et d'intégration
# Framework : pytest + pytest-django
# =================================================================

from datetime import timedelta
from decimal import Decimal

import factory
import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker

from .models import (
    Chantier,
    Lot,
    Tache,
    HeureTravail,
    Equipe,
    Membre,
    StatusChantier,
    StatusTache,
    RoleMembre,
    TypeSousTraitant
)

fake = Faker('fr_FR')


# =================================================================
# FACTORIES - Génération de données de test
# =================================================================


class UserFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des utilisateurs de test."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class ChantiersFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des chantiers de test."""

    class Meta:
        model = Chantier

    numero = factory.Sequence(lambda n: f'CH-{n:04d}')
    nom = factory.Faker('sentence', nb_words=4)
    adresse = factory.Faker('address')
    codepostal = factory.Faker('postcode')
    ville = factory.Faker('city')
    date_debut = factory.Faker('date_object')
    date_fin_prevue = factory.Faker('date_object')
    status = StatusChantier.EN_COURS
    chef = factory.SubFactory(UserFactory)
    creé_par = factory.SubFactory(UserFactory)
    budget_total = Decimal('50000.00')


class MembreFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des membres d'équipe."""

    class Meta:
        model = Membre

    prenom = factory.Faker('first_name')
    nom = factory.Faker('last_name')
    email = factory.Faker('email')
    role = RoleMembre.OUVRIER
    taux_horaire = Decimal('50.00')
    date_embauche = factory.Faker('date_object')
    user = factory.SubFactory(UserFactory)


class EquipeFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des équipes."""

    class Meta:
        model = Equipe

    nom = factory.Sequence(lambda n: f'Équipe {n}')
    specialite = TypeSousTraitant.MACONNERIE
    chef = factory.SubFactory(MembreFactory)


class LotFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des lots."""

    class Meta:
        model = Lot

    chantier = factory.SubFactory(ChantiersFactory)
    nom = factory.Faker('sentence', nb_words=3)
    numero = factory.Sequence(lambda n: n + 1)
    date_debut_prevue = factory.Faker('date_object')
    date_fin_prevue = factory.Faker('date_object')
    budget_lot = Decimal('10000.00')
    status = StatusChantier.EN_COURS


class TacheFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des tâches."""

    class Meta:
        model = Tache

    lot = factory.SubFactory(LotFactory)
    numero = factory.Sequence(lambda n: f'T-{n:03d}')
    nom = factory.Faker('sentence', nb_words=3)
    ordre = factory.Sequence(lambda n: n)
    date_debut_prevue = factory.Faker('date_object')
    date_fin_prevue = factory.Faker('date_object')
    status = StatusTache.A_FAIRE
    heures_estimees = Decimal('40.00')
    taux_horaire = Decimal('50.00')
    equipe = factory.SubFactory(EquipeFactory)


# =================================================================
# TESTS DE MODÈLES
# =================================================================


@pytest.mark.django_db
class TestChantierModel:
    """Tests du modèle Chantier."""

    def test_creer_chantier(self):
        """Créer un chantier avec données valides."""
        chantier = ChantiersFactory()
        assert chantier.id is not None
        assert chantier.numero is not None
        assert chantier.actif is True

    def test_progression_chantier(self):
        """Calculer la progression d'un chantier."""
        chantier = ChantiersFactory()
        lot = LotFactory(chantier=chantier)
        TacheFactory(lot=lot, status=StatusTache.A_FAIRE)
        TacheFactory(lot=lot, status=StatusTache.TERMINEE)

        progression = chantier.get_progression_percentage()
        assert progression == 50.0  # 1 tâche terminée sur 2

    def test_cout_reel_chantier(self):
        """Calculer le coût réel du chantier."""
        chantier = ChantiersFactory()
        lot = LotFactory(chantier=chantier)
        tache = TacheFactory(
            lot=lot,
            heures_reelles=Decimal('10.0'),
            taux_horaire=Decimal('100.00')
        )

        cout = tache.calculer_cout_heures()
        assert cout == Decimal('1000.00')


@pytest.mark.django_db
class TestTacheModel:
    """Tests du modèle Tâche."""

    def test_creer_tache(self):
        """Créer une tâche valide."""
        tache = TacheFactory()
        assert tache.id is not None
        assert tache.status == StatusTache.A_FAIRE

    def test_tache_en_retard(self):
        """Détecter une tâche en retard."""
        # Tâche avec date de fin passée
        tache = TacheFactory(
            date_fin_prevue=timezone.now().date() - timedelta(days=1),
            status=StatusTache.EN_COURS
        )

        assert tache.est_en_retard() is True

    def test_calculer_heures_tache(self):
        """Mettre à jour les heures réelles d'une tâche."""
        tache = TacheFactory(heures_reelles=Decimal('0'))
        membre = MembreFactory()

        # Ajouter des heures
        HeureTravail.objects.create(
            tache=tache,
            membre=membre,
            heures=Decimal('8.5'),
            date=timezone.now().date()
        )

        tache.calculer_heures_reelles()
        assert tache.heures_reelles == Decimal('8.5')


@pytest.mark.django_db
class TestHeureTravailModel:
    """Tests du modèle HeureTravail."""

    def test_creer_entree_heures(self):
        """Créer une entrée d'heures."""
        tache = TacheFactory()
        membre = MembreFactory()

        heures = HeureTravail.objects.create(
            tache=tache,
            membre=membre,
            heures=Decimal('8.0'),
            date=timezone.now().date()
        )

        assert heures.id is not None
        assert heures.heures == Decimal('8.0')

    def test_validation_heures_positives(self):
        """Les heures doivent être positives."""
        tache = TacheFactory()
        membre = MembreFactory()

        with pytest.raises(Exception):
            HeureTravail.objects.create(
                tache=tache,
                membre=membre,
                heures=Decimal('-5.0')
            )


# =================================================================
# TESTS API (DRF)
# =================================================================


@pytest.mark.django_db
class TestChantiersAPI:
    """Tests des endpoints de chantiers."""

    def test_list_chantiers_sans_auth(self, client):
        """Listing sans authentification doit retourner 401."""
        response = client.get('/api/v1/chantiers/')
        assert response.status_code == 401

    @pytest.fixture
    def api_client_auth(self):
        """Client authentifié."""
        from rest_framework.test import APIClient

        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        return client

    def test_list_chantiers_avec_auth(self, api_client_auth):
        """Listing avec authentification."""
        ChantiersFactory.create_batch(3)
        response = api_client_auth.get('/api/v1/chantiers/')

        assert response.status_code == 200
        assert len(response.data['results']) == 3

    def test_creer_chantier(self, api_client_auth):
        """Créer un chantier via API."""
        from datetime import date

        data = {
            'numero': 'CH-TEST-001',
            'nom': 'Test Chantier',
            'adresse': '123 rue de Test',
            'codepostal': '69000',
            'ville': 'Lyon',
            'date_debut': date.today().isoformat(),
            'date_fin_prevue': (
                date.today() + timedelta(days=30)
            ).isoformat(),
            'budget_total': '50000.00'
        }

        response = api_client_auth.post(
            '/api/v1/chantiers/',
            data,
            format='json'
        )

        assert response.status_code == 201
        assert response.data['numero'] == 'CH-TEST-001'

    def test_rapport_chantier(self, api_client_auth):
        """Endpoint rapport du chantier."""
        chantier = ChantiersFactory()
        response = api_client_auth.get(
            f'/api/v1/chantiers/{chantier.id}/rapport/'
        )

        assert response.status_code == 200
        assert 'progression_percentage' in response.data
        assert 'cout_reel' in response.data


@pytest.mark.django_db
class TestTachesAPI:
    """Tests des endpoints de tâches."""

    @pytest.fixture
    def api_client_auth(self):
        from rest_framework.test import APIClient

        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        return client

    def test_enregistrer_heures(self, api_client_auth):
        """Enregistrer des heures via l'API mobile."""
        tache = TacheFactory()
        membre = MembreFactory()

        data = {
            'membre': membre.id,
            'heures': '8.5',
            'description': 'Travaux de maçonnerie',
            'latitude': 45.123456,
            'longitude': 5.123456
        }

        response = api_client_auth.post(
            f'/api/v1/taches/{tache.id}/heures/',
            data,
            format='json'
        )

        assert response.status_code == 201
        assert response.data['heures'] == 8.5

    def test_upload_photo(self, api_client_auth):
        """Upload d'une photo (MOBILE)."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        tache = TacheFactory()

        # Créer une fausse image
        image_content = b'fake image content'
        image = SimpleUploadedFile(
            'test.jpg',
            image_content,
            content_type='image/jpeg'
        )

        data = {
            'titre': 'Photo avant',
            'description': 'État avant travaux',
            'image': image,
            'latitude': 45.123456,
            'longitude': 5.123456
        }

        response = api_client_auth.post(
            f'/api/v1/taches/{tache.id}/photo/',
            data,
            format='multipart'
        )

        assert response.status_code == 201


# =================================================================
# TESTS DE PERFORMANCE
# =================================================================


@pytest.mark.django_db
class TestPerformance:
    """Tests de performance et N+1 queries."""

    def test_no_n_plus_1_list_chantiers(self, django_assert_num_queries):
        """Vérifier que list chantiers n'a pas N+1 queries."""
        # Créer des chantiers
        ChantiersFactory.create_batch(5)

        # Les requêtes doivent être minimales
        with django_assert_num_queries(5):  # Approximatif
            chantiers = list(Chantier.objects.select_related('chef'))
            for c in chantiers:
                _ = c.chef.username  # Accéder au chef


# =================================================================
# COMMANDES POUR LANCER LES TESTS
# =================================================================

"""
# Lancer tous les tests
pytest

# Tests avec couverture
pytest --cov=chantiers

# Tests spécifiques
pytest chantiers/tests.py::TestChantierModel::test_creer_chantier -v

# Tests API uniquement
pytest -k "API" -v

# Tests avec débuggage
pytest -vv --pdb

# Tests en parallèle
pytest -n 4
"""
