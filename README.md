# SENTINEL-X — Workshop EPSI M1 2026

Ce dépôt contient les développements réalisés pour le projet **SENTINEL-X** dans le cadre du Workshop EPSI M1 2026, équipe G3.

SENTINEL-X est un système de supervision destiné à surveiller un environnement industriel à l'aide d'un **boîtier de surveillance** équipé de plusieurs capteurs et d'une webcam USB connectée au PC serveur.

Les développements présentés dans ce dépôt concernent principalement le **dashboard de supervision**, le **serveur caméra USB**, la **détection de personnes avec YOLOv8n** et l'intégration de ces éléments dans l'infrastructure du projet.

## Fonctionnalités développées

Les principales fonctionnalités développées sont :

* dashboard web de supervision ;
* affichage de l'état du boîtier de surveillance ;
* affichage de l'état du réseau ;
* affichage de l'état des capteurs ;
* affichage des données environnementales ;
* graphiques des données en temps réel ;
* réception des données via WebSocket ;
* affichage des événements ;
* commande du buzzer depuis l'interface ;
* affichage du flux de la webcam USB ;
* détection de personnes avec YOLOv8n ;
* génération d'événements lors d'une détection ;
* thème sombre ;
* thème clair ;
* mémorisation du thème choisi ;
* conteneurisation de l'interface avec nginx ;
* intégration de l'interface dans l'infrastructure Docker.

## Architecture générale

```text
                         ┌──────────────────────┐
                         │  Boîtier de          │
                         │  surveillance        │
                         │  Capteurs            │
                         └──────────┬───────────┘
                                    │
                                   MQTT
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Broker Mosquitto   │
                         │        Docker        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Système central    │
                         │    REST / WebSocket  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      Dashboard       │
                         │   React / TypeScript │
                         └──────────────────────┘


                         ┌──────────────────────┐
                         │      Webcam USB      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Python / OpenCV   │
                         │       YOLOv8n        │
                         └──────────┬───────────┘
                                    │
                             Détection personne
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      Dashboard       │
                         └──────────────────────┘
```

Le système repose sur deux flux principaux.

Le premier concerne les données du boîtier de surveillance. Les mesures des capteurs sont transmises au système central, puis mises à disposition du dashboard.

Le second concerne la surveillance vidéo. La webcam USB est connectée directement au PC serveur. Le flux est capturé et traité localement avec Python, OpenCV et YOLOv8n avant d'être exploité par le dashboard.

## Dashboard de supervision

Le dashboard est développé avec :

* React ;
* TypeScript ;
* Vite ;
* Recharts ;
* nginx.

L'interface regroupe les informations principales du système sur une seule page.

### Supervision

La section de supervision permet notamment de visualiser :

* l'état du boîtier de surveillance ;
* l'état du réseau ;
* l'état des capteurs ;
* le nombre d'événements reçus ;
* la disponibilité du système ;
* la commande du buzzer.

L'état du boîtier de surveillance est déterminé à partir de la réception des dernières données du système.

### Données environnementales

Les données des capteurs sont représentées sous forme de graphiques.

Les données exploitées sont notamment :

* température ;
* humidité ;
* valeur brute du capteur de gaz.

Le dashboard conserve au maximum les **30 dernières mesures** pour l'affichage.

Lorsqu'une nouvelle mesure est reçue, elle est ajoutée à l'historique affiché. Lorsque la limite de 30 mesures est atteinte, la mesure la plus ancienne est supprimée.

```text
Mesures reçues

1 → 2 → 3 → ... → 30

Nouvelle mesure

2 → 3 → ... → 30 → 31
```

Cette limitation permet de conserver un affichage lisible et réactif.

### Événements

Les événements reçus par le système sont pris en compte par l'interface de supervision.

Les événements peuvent notamment provenir du module de vision artificielle.

Le type d'événement utilisé pour une détection de personne est :

```text
person_detected
```

### Commande du buzzer

Un bouton permet de commander le buzzer du boîtier de surveillance depuis le dashboard.

La commande utilise notamment les paramètres suivants :

```text
device_id
target : buzzer
state : true
duration_ms : 3000
```

Le buzzer est ainsi activé pendant une durée de **3 secondes**.

Le bouton est désactivé lorsqu'aucun boîtier n'est disponible ou lorsqu'une commande est déjà en cours de traitement.

## Communication temps réel

Le dashboard utilise une connexion **WebSocket** afin de recevoir les nouvelles données sans nécessiter de rechargement de la page.

Le fonctionnement général est le suivant :

```text
Nouvelle donnée
      │
      ▼
  WebSocket
      │
      ▼
    React
      │
      ├── Mise à jour des mesures
      ├── Mise à jour de l'état du système
      ├── Mise à jour des événements
      └── Mise à jour du graphique
```

Une reconnexion automatique est prévue lorsque la connexion WebSocket est interrompue.

## Caméra USB

La surveillance vidéo utilise une webcam USB connectée directement au PC serveur.

La capture est réalisée en Python avec OpenCV.

La configuration actuelle est :

```text
Résolution : 640 × 480
FPS cible  : 25
```

La webcam est capturée directement par le serveur et ne dépend pas de la caméra du navigateur.

Le serveur caméra fournit notamment les fonctionnalités suivantes :

```text
/camera/stream
/camera/snapshot
/health
```

### Flux vidéo

La fonctionnalité `/camera/stream` fournit le flux vidéo continu utilisé par le dashboard.

La fonctionnalité `/camera/snapshot` permet de récupérer une image instantanée de la caméra.

La fonctionnalité `/health` permet de vérifier l'état du serveur caméra, notamment la disponibilité de la webcam et le chargement du modèle YOLO.

## Intelligence artificielle

La détection vidéo utilise **YOLOv8n** avec la bibliothèque Ultralytics.

Le modèle utilisé est :

```text
yolov8n.pt
```

L'objectif actuel est uniquement de détecter les personnes présentes devant la caméra.

La détection est donc limitée à la classe :

```text
person
```

La configuration actuelle est :

```text
Classe détectée       : person
Confiance minimale    : 0.5
Intervalle d'analyse  : 0.2 seconde
```

L'intervalle de 0,2 seconde correspond à environ **5 analyses par seconde**.

Lorsqu'une personne est détectée, YOLOv8n génère une détection autour de celle-ci et l'image affichée peut être annotée avec le résultat de l'analyse.

## Génération des événements IA

Lorsqu'une personne est détectée, le serveur caméra génère un événement à destination du système central.

Le type d'événement utilisé est :

```text
person_detected
```

L'événement contient notamment :

* le type de détection ;
* la source `vision` ;
* le niveau de confiance ;
* les informations relatives à la détection.

Un délai de **5 secondes** est appliqué entre deux événements du même type.

Ce mécanisme évite de générer continuellement des événements lorsqu'une même personne reste présente devant la caméra.

```text
Personne détectée
       │
       ▼
person_detected
       │
       ▼
Événement envoyé
       │
       ▼
Délai de 5 secondes
       │
       ▼
Nouvelle détection autorisée
```

## Traitement local de l'IA

La détection YOLO est exécutée directement sur le PC serveur.

Le traitement est réalisé selon le flux suivant :

```text
Webcam USB
    │
    ▼
OpenCV
    │
    ▼
Image capturée
    │
    ▼
YOLOv8n
    │
    ▼
Détection de personne
    │
    ├── Événement person_detected
    │
    └── Image annotée
             │
             ▼
         Dashboard
```

Aucun service d'intelligence artificielle distant n'est nécessaire pour effectuer la détection.

Le traitement de la vidéo et l'inférence YOLO sont réalisés localement sur le PC serveur.

## Thème de l'interface

Le dashboard possède deux thèmes :

* thème sombre ;
* thème clair.

Le changement de thème est disponible directement depuis l'interface.

Le choix est enregistré dans le stockage local du navigateur afin de conserver la préférence lors des prochaines ouvertures du dashboard.

## Infrastructure

L'interface est conteneurisée avec Docker.

Le serveur caméra Python est exécuté directement sur le PC serveur afin d'accéder à la webcam USB.

L'infrastructure Docker Compose comprend notamment :

| Service             |        Port | Accès             | Rôle                          |
| ------------------- | ----------: | ----------------- | ----------------------------- |
| Mosquitto           |        8883 | Hôte              | Broker MQTT sécurisé          |
| Mosquitto WebSocket |        9001 | Local uniquement  | Communication MQTT WebSocket  |
| API                 |        8000 | Hôte              | Communication avec le système |
| Interface           | 8081 / 8443 | Hôte              | Dashboard HTTP / HTTPS        |
| PostgreSQL          |        5432 | Docker uniquement | Base de données               |
| Grafana             |        3000 | Local uniquement  | Visualisation du monitoring   |
| Prometheus          |        9090 | Local uniquement  | Collecte des métriques        |
| cAdvisor            |        8080 | Docker uniquement | Métriques des conteneurs      |

PostgreSQL n'est pas directement exposé sur le réseau local.

Les services de monitoring Grafana et Prometheus sont également limités à un accès local.

### Réseaux Docker

Les services Docker sont répartis sur plusieurs réseaux afin d'isoler les communications entre les composants.

Le réseau utilisé pour les communications liées à MQTT est :

```text
172.28.1.0/24
```

Le réseau dédié à la base de données PostgreSQL est :

```text
172.28.2.0/24
```

Le réseau de la base de données est configuré comme réseau interne et n'est pas directement accessible depuis l'extérieur de l'infrastructure Docker.


## Communication avec le système central

Le dashboard communique avec le système central afin de :

* récupérer les mesures ;
* recevoir les nouvelles données en temps réel ;
* récupérer l'état des boîtiers ;
* recevoir les événements ;
* transmettre les commandes du buzzer.

Les principales communications utilisées par le dashboard sont :

```text
/api/readings
/api/commands
/ws
```

Les communications avec l'API utilisent HTTPS.

La communication WebSocket permet de recevoir les nouvelles données et événements en temps réel.

Le serveur caméra est utilisé séparément pour récupérer le flux vidéo et l'état de la webcam.

## Interface nginx

L'interface React est construite puis servie par nginx dans un conteneur Docker.

Le conteneur utilise les ports internes :

```text
80
443
```

Ils correspondent respectivement aux accès HTTP et HTTPS.

Les ports sont publiés sur le PC serveur de la manière suivante :

```text
8081 → 80
8443 → 443
```

Le dashboard est donc accessible avec :

```text
http://localhost:8081
https://localhost:8443
```

nginx permet de servir les fichiers générés par Vite et de fournir l'accès HTTP/HTTPS au dashboard.

## Monitoring

L'infrastructure utilise plusieurs composants de monitoring.

### Prometheus

Prometheus collecte les métriques des composants de l'infrastructure.

Il est accessible localement sur :

```text
http://127.0.0.1:9090
```

### Grafana

Grafana permet de visualiser les métriques collectées par Prometheus.

Il est accessible localement sur :

```text
http://127.0.0.1:3000
```

### cAdvisor

cAdvisor fournit des métriques relatives aux conteneurs Docker, notamment concernant l'utilisation de leurs ressources.

Son port n'est pas publié directement sur le PC serveur.

## Sécurité

Aucun secret ne doit être présent en clair dans le dépôt.

Les informations sensibles utilisées par l'infrastructure doivent rester dans l'environnement local, notamment :

```text
.env
docker-compose.override.yml
```

Les éléments suivants ne doivent jamais être ajoutés au dépôt Git :

* mots de passe ;
* tokens d'authentification ;
* clés privées ;
* fichiers `.env` contenant des secrets.

Les communications MQTT utilisent TLS.

Les accès HTTPS du dashboard utilisent également des certificats TLS.

Les clés privées utilisées par ces services doivent rester uniquement dans l'environnement local et ne doivent pas être incluses dans l'archive finale.

### Limites de sécurité actuelles

Dans l'état actuel du projet :

* le dashboard est accessible en HTTP et en HTTPS ;
* l'API utilise HTTPS ;
* le flux caméra utilise actuellement HTTP ;
* les mécanismes d'authentification et de restriction d'accès doivent être renforcés avant une utilisation en production ;
* les certificats et clés privées doivent rester dans l'environnement local.

## Structure du dépôt

```text
.
├── README.md
├── api/
│   ├── Dockerfile
│   ├── database.py
│   ├── factory.py
│   ├── hub.py
│   ├── main.py
│   ├── models/
│   │   ├── db_models.py
│   │   └── models.py
│   ├── mqtt_bridge.py
│   └── requirements.txt
├── arduino_sentinel/
│   └── arduino_sentinel.ino
├── camera/
│   ├── camera.py
│   └── requirements.txt
├── infra/
│   ├── docker-compose.yml
│   ├── buzzer.ps1
│   ├── listen.ps1
│   ├── simulate-esp.ps1
│   ├── mosquitto/
│   │   ├── certs/
│   │   └── config/
│   └── prometheus/
│       └── prometheus.yml
├── interface/
│   ├── certs/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CameraFeed.tsx
│   │   │   ├── EnvironmentChart.tsx
│   │   │   ├── Header.tsx
│   │   │   └── SystemStatus.tsx
│   │   ├── App.tsx
│   │   ├── index.css
│   │   ├── main.tsx
│   │   └── types.ts
│   ├── Dockerfile
│   ├── eslint.config.js
│   ├── index.html
│   ├── nginx.conf.template
│   ├── package-lock.json
│   ├── package.json
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
└── start-sentinel.ps1
```

Les clés privées et les fichiers contenant des secrets ne doivent pas apparaître dans cette structure de l'archive finale.

## Dossier `camera/`

Le dossier `camera/` contient le serveur Python utilisé pour la surveillance vidéo.

Il permet :

* d'ouvrir la webcam USB ;
* de capturer les images avec OpenCV ;
* de détecter les personnes avec YOLOv8n ;
* de produire un flux vidéo ;
* de fournir un snapshot ;
* de vérifier l'état de la caméra ;
* de générer les événements de détection.

Les principales dépendances sont :

```text
fastapi
uvicorn
opencv-python
requests
ultralytics
```

## Dossier `interface/`

Le dossier `interface/` contient le dashboard React/TypeScript.

Les principaux composants sont :

```text
src/
├── components/
│   ├── CameraFeed.tsx
│   ├── EnvironmentChart.tsx
│   ├── Header.tsx
│   └── SystemStatus.tsx
├── App.tsx
├── index.css
├── main.tsx
└── types.ts
```

### `App.tsx`

Le composant principal gère notamment :

* le chargement de l'historique des données ;
* la connexion WebSocket ;
* la réception des nouvelles mesures ;
* la réception des événements ;
* l'état des boîtiers de surveillance ;
* la gestion du thème.

### `CameraFeed.tsx`

Le composant `CameraFeed` affiche :

* le flux vidéo ;
* l'état de disponibilité de la caméra ;
* un affichage de remplacement lorsque la caméra est indisponible.

### `EnvironmentChart.tsx`

Le composant `EnvironmentChart` représente les données environnementales sous forme de graphiques.

Les mesures affichées sont limitées aux 30 dernières valeurs.

### `SystemStatus.tsx`

Le composant `SystemStatus` affiche notamment :

* l'état du boîtier de surveillance ;
* l'état du réseau ;
* l'état des capteurs ;
* les informations relatives aux événements ;
* la commande du buzzer.

## Installation de la caméra

Depuis le dossier `camera`, installer les dépendances :

```powershell
py -m pip install -r requirements.txt
```

Vérifier ensuite que YOLO est correctement installé :

```powershell
py -c "from ultralytics import YOLO; print('YOLO OK')"
```

## Démarrage du serveur caméra

Depuis le dossier `camera` :

```powershell
py -m uvicorn camera:app --host 0.0.0.0 --port 8001
```

Le serveur caméra est alors disponible sur :

```text
http://localhost:8001
```

## Vérification de la caméra

Pour vérifier l'état du serveur caméra :

```powershell
curl http://localhost:8001/health
```

Une réponse similaire à la suivante est attendue :

```json
{
    "status": "ok",
    "camera": 1,
    "camera_open": true,
    "yolo_loaded": true
}
```

La valeur `camera_open` indique si la webcam est actuellement accessible.

La valeur `yolo_loaded` indique si le modèle YOLOv8n a été chargé correctement.

## Démarrage de l'infrastructure

Depuis le dossier `infra`, créer le fichier `.env` à partir du modèle fourni par le projet.

Sous PowerShell :

```powershell
Copy-Item .env.example .env
```

Renseigner ensuite les variables nécessaires dans `.env`.

Les valeurs sensibles doivent rester uniquement dans ce fichier local.

Démarrer les services :

```powershell
docker compose up -d --build
```

Vérifier l'état des conteneurs :

```powershell
docker compose ps
```

## Accès aux services

Une fois l'infrastructure démarrée :

Dashboard HTTP :

```text
http://localhost:8081
```

Dashboard HTTPS :

```text
https://localhost:8443
```

API HTTPS :

```text
https://localhost:8000
```

Serveur caméra HTTP :

```text
http://localhost:8001
```

Grafana :

```text
http://127.0.0.1:3000
```

Prometheus :

```text
http://127.0.0.1:9090
```

Broker MQTT sécurisé :

```text
8883
```

## Démarrage complet

Le script PowerShell `start-sentinel.ps1`, situé à la racine du projet, permet de faciliter le démarrage du serveur caméra et de l'infrastructure Docker.

Le lancement manuel reste possible avec les commandes présentées précédemment.

## Limites connues

Les limites actuelles du projet sont :

* la webcam doit être connectée directement au PC serveur ;
* l'index de la webcam peut varier selon le périphérique utilisé ;
* la caméra utilise actuellement l'index `1` ;
* la détection IA est limitée à la classe `person` ;
* les performances de YOLOv8n dépendent des ressources disponibles sur le PC serveur ;
* le traitement vidéo est effectué localement ;
* le flux caméra utilise actuellement HTTP ;
* l'environnement réseau dépend de la configuration du Workshop ;
* les certificats et secrets doivent être fournis séparément et ne doivent pas être inclus dans l'archive Git.

## Vérification avant remise

Avant de créer l'archive finale, vérifier l'état du dépôt :

```powershell
git status
```

Vérifier les fichiers suivis :

```powershell
git ls-files
```

Vérifier notamment qu'aucun élément sensible n'est présent dans les fichiers suivis :

```text
.env
*.key
*.pem
mots de passe
tokens
clés privées
```

Les fichiers nécessaires au fonctionnement local mais exclus de Git doivent rester exclus de l'archive finale.

Les fichiers temporaires ou générés automatiquement ne doivent pas être inclus dans le rendu.

## Création de l'archive

L'archive demandée doit respecter le nom :

```text
Workshop2026-M1-G3-Code.zip
```

Une fois les modifications commitées, l'archive peut être générée avec :

```powershell
git archive --format=zip --output=Workshop2026-M1-G3-Code.zip HEAD
```

Cette commande génère une archive à partir des fichiers suivis par Git.

Il est recommandé de vérifier le contenu de l'archive avant de la transmettre.

## Équipe

**Workshop EPSI M1 2026 — Groupe G3**

Membres du groupe :

```text
Martin RANDOUX
Thimoté CABOTTE
Mathis THIBAUT
Yasmine LAAROUSSI
...
```

## Contexte et utilisation

Projet réalisé dans le cadre pédagogique du Workshop EPSI M1 2026.

Le projet et ses composants sont destinés à l'environnement de démonstration et d'évaluation du Workshop.
