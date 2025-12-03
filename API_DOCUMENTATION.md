# ============================================================================
# API DOCUMENTATION - Endpoints et Exemples
# ============================================================================

## 🚀 Endpoints API Complets

### BASE URL
```
http://localhost:8000/api/v1/
```

### AUTHENTIFICATION
Toutes les requêtes nécessitent un Token Bearer :
```
Authorization: Token YOUR_API_TOKEN
```

Obtenir un token :
```bash
curl -X POST http://localhost:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

---

## 📋 ENDPOINTS CHANTIERS

### 1️⃣ Lister tous les chantiers
```
GET /chantiers/
```

**Filtres disponibles :**
- `status` : EN_ATTENTE, EN_COURS, EN_PAUSE, TERMINE, FACTURE, ANNULE
- `ville` : Chercher par ville
- `date_debut_after` : A partir d'une date
- `budget_min` / `budget_max` : Plage de budget
- `en_retard` : true/false

**Exemple :**
```bash
curl -X GET "http://localhost:8000/api/v1/chantiers/?status=EN_COURS&ville=Lyon" \
  -H "Authorization: Token YOUR_TOKEN"
```

**Réponse :**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "numero": "CH-2024-001",
      "nom": "Rénovation Maison Martin",
      "status": "EN_COURS",
      "progression": 45.2,
      "budget_total": "50000.00",
      "cout_reel": "32450.50",
      "jours_restants": 15,
      "date_creation": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### 2️⃣ Créer un chantier
```
POST /chantiers/
```

**Données requises :**
```json
{
  "numero": "CH-2024-NEW",
  "nom": "Nouveau Chantier",
  "adresse": "123 rue de la Paix",
  "codepostal": "69000",
  "ville": "Lyon",
  "date_debut": "2024-02-01",
  "date_fin_prevue": "2024-08-31",
  "budget_total": "75000.00",
  "description": "Description du chantier",
  "chef": 5
}
```

**Exemple :**
```bash
curl -X POST http://localhost:8000/api/v1/chantiers/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{\n    "numero": "CH-2024-NEW",\n    "nom": "Nouveau Chantier",\n    "adresse": "123 rue de la Paix",\n    "codepostal": "69000",\n    "ville": "Lyon",\n    "date_debut": "2024-02-01",\n    "date_fin_prevue": "2024-08-31",\n    "budget_total": "75000.00"\n  }'
```

---

### 3️⃣ Récupérer détail d'un chantier
```
GET /chantiers/{id}/
```

**Exemple :**
```bash
curl -X GET http://localhost:8000/api/v1/chantiers/1/ \
  -H "Authorization: Token YOUR_TOKEN"
```

**Réponse :** (Inclut les lots imbriqués)
```json
{
  "id": 1,
  "numero": "CH-2024-001",
  "nom": "Rénovation Maison Martin",
  "lots": [
    {
      "id": 1,
      "numero": 1,
      "nom": "Démolition intérieure",
      "date_fin_prevue": "2024-03-01",
      "status": "EN_COURS",
      "progression": 60.0
    }
  ]
}
```

---

### 4️⃣ Rapport complet d'un chantier
```
GET /chantiers/{id}/rapport/
```

**Réponse :** (Données pour dashboard/reporting)
```json
{
  "chantier": {...},
  "lots": [...],
  "taches_totales": 25,
  "taches_terminees": 12,
  "progression_percentage": 48.0,
  "heures_estimees": "520.0",
  "heures_reelles": "380.5",
  "cout_previsionnel": "50000.00",
  "cout_reel": "32450.50",
  "anomalies_ouvertes": 3,
  "membres_actifs": 8
}
```

---

## 🎯 ENDPOINTS TÂCHES (Point focal mobile)

### 1️⃣ Lister les tâches
```
GET /taches/?lot_id=1&status=EN_COURS
```

**Filtres :**
- `lot_id` : Filtrer par lot
- `chantier_id` : Filtrer par chantier
- `status` : A_FAIRE, EN_COURS, EN_ATTENTE, TERMINEE, REVISEE
- `en_retard` : true/false

---

### 2️⃣ Enregistrer des heures (MOBILE) 🔑
```
POST /taches/{id}/heures/
```

**Données :**
```json
{
  "membre": 5,
  "heures": 8.5,
  "description": "Travaux de maçonnerie - phase 1",
  "latitude": 45.123456,
  "longitude": 5.123456
}
```

**Exemple (avec cURL) :**
```bash
curl -X POST http://localhost:8000/api/v1/taches/1/heures/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{\n    "membre": 5,\n    "heures": 8.5,\n    "description": "Travaux maçonnerie",\n    "latitude": 45.123456,\n    "longitude": 5.123456\n  }'
```

**Réponse :**
```json
{
  "id": 42,
  "tache": 1,
  "membre": 5,
  "date": "2024-01-20",
  "heures": 8.5,
  "description": "Travaux de maçonnerie - phase 1",
  "latitude": 45.123456,
  "longitude": 5.123456,
  "validee": false,
  "date_enregistrement": "2024-01-20T14:30:00Z"
}
```

---

### 3️⃣ Upload photo (MOBILE) 📸
```
POST /taches/{id}/photo/
```

**Données (multipart/form-data) :**
```
image: <fichier image>
titre: "Photo avant"
description: "État avant les travaux"
latitude: 45.123456
longitude: 5.123456
```

**Exemple (avec cURL) :**
```bash
curl -X POST http://localhost:8000/api/v1/taches/1/photo/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "image=@/path/to/photo.jpg" \
  -F "titre=Photo avant" \
  -F "description=État avant" \
  -F "latitude=45.123456" \
  -F "longitude=5.123456"
```

**Réponse :**
```json
{
  "id": 15,
  "tache": 1,
  "titre": "Photo avant",
  "description": "État avant les travaux",
  "image": "https://example.com/media/chantiers/photos/2024/01/20/photo_abc.jpg",
  "latitude": 45.123456,
  "longitude": 5.123456,
  "date_photo": "2024-01-20T14:35:00Z",
  "approuvee": false,
  "uploadée_par": 3,
  "date_upload": "2024-01-20T14:36:00Z"
}
```

---

### 4️⃣ Signaler une anomalie (MOBILE) ⚠️
```
POST /taches/{id}/signaler_anomalie/
```

**Données :**
```json
{
  "titre": "Malfaçon détectée",
  "description": "Joints mal étanchéifiés au coin nord-est",
  "severite": "MAJEURE",
  "photo": 15
}
```

---

### 5️⃣ Récupérer heures de la tâche
```
GET /taches/{id}/heures/
```

**Réponse :** (Liste historique d'heures)
```json
[
  {
    "id": 42,
    "tache": 1,
    "membre": {"id": 5, "prenom": "Jean", "nom": "Dupont"},
    "date": "2024-01-20",
    "heures": 8.5,
    "validee": true
  },
  {
    "id": 41,
    "tache": 1,
    "membre": {"id": 6, "prenom": "Pierre", "nom": "Martin"},
    "date": "2024-01-20",
    "heures": 7.0,
    "validee": false
  }
]
```

---

## 👥 ENDPOINTS ÉQUIPES & MEMBRES

### 1️⃣ Lister les équipes
```
GET /equipes/
```

### 2️⃣ Lister les membres
```
GET /membres/?equipe=1&role=OUVRIER
```

### 3️⃣ Mes heures ce mois-ci
```
GET /heures_travail/mes_heures/
```

**Réponse :**
```json
{
  "heures": [...],
  "total_heures": 160.5,
  "mois": "January 2024"
}
```

---

## 📊 ENDPOINTS RAPPORTS & VALIDATION

### 1️⃣ Valider des heures (CHEF uniquement)
```
POST /heures_travail/{id}/valider/
```

### 2️⃣ Lister anomalies du chantier
```
GET /chantiers/{id}/anomalies/?statut=OUVERTE
```

### 3️⃣ Assigner anomalie
```
POST /anomalies/{id}/assigner/
```

**Données :**
```json
{
  "responsable_id": 7
}
```

### 4️⃣ Fermer anomalie
```
POST /anomalies/{id}/fermer/
```

---

## 📱 CAS D'USAGE MOBILE

### Workflow chef de chantier terrain

```mermaid
1. Récup tâches du jour
   GET /taches/?chantier_id=1&date=today

2. Pour chaque équipe :
   a) Saisir les heures
      POST /taches/{id}/heures/
   
   b) Prendre photo
      POST /taches/{id}/photo/
   
   c) Signaler anomalie (si besoin)
      POST /taches/{id}/signaler_anomalie/

3. Rapport d'avancement
   GET /chantiers/{id}/rapport/
```

### Code exemple (React Native / Flutter)

```javascript
// Enregistrer heures + géolocalisation
const enregistrerHeures = async (tacheId, heures, coords) => {
  const response = await fetch(
    `${API_BASE}/taches/${tacheId}/heures/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        membre: memberId,
        heures: heures,
        description: description,
        latitude: coords.latitude,
        longitude: coords.longitude
      })
    }
  );
  return response.json();
};
```

---

## 🔒 Codes HTTP

| Code | Signification |
|------|---------------|
| 200 | ✅ OK |
| 201 | ✅ Créé |
| 400 | ❌ Erreur validation |
| 401 | ❌ Non authentifié |
| 403 | ❌ Permission refusée |
| 404 | ❌ Non trouvé |
| 500 | ❌ Erreur serveur |

---

## 📖 Documentation interactive

Swagger : `http://localhost:8000/api/v1/schema/swagger/`  
ReDoc : `http://localhost:8000/api/v1/schema/redoc/`
