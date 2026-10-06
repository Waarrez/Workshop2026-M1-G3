# Sentinel - Infrastructure & Monitoring

Ce répertoire contient la configuration complète de l'infrastructure Docker pour le projet Sentinel.

## Architecture des Services

| Service | Port Externe | Port Interne | Rôle |
| :--- | :--- | :--- | :--- |
| **mosquitto** | 8883 | 8883 | Broker MQTT sécurisé (TLS/MQTTS) |
| **api** | 8000 | 8000 | API FastAPI (Backend) |
| **db** | - | 5432 | Base de données PostgreSQL (réseau interne isolé) |
| **grafana** | 3000 | 3000 | Tableaux de bord & métriques de supervision |
| **prometheus** | 9090 | 9090 | Collecteur de séries temporelles & métriques |
| **cadvisor** | - | 8080 | Exportateur des métriques conteneurs pour Prometheus |

## Réseau & Sécurité

- Réseau MQTT : 172.28.1.0/24
- Réseau DB (Isolé) : 172.28.2.0/24 (internal: true)
- Accès ESP8266 : IP Hotspot 192.168.137.1, Port MQTTS 8883 (règle Pare-feu Windows active).

## Démarrage Rapide

\\\ash
# 1. Copier le modèle d'environnement
cp .env.example .env

# 2. Démarrer l'ensemble de la stack
docker compose up -d
\\\

## Monitoring & Supervision

- Grafana : http://localhost:3000 (Identifiants : admin / Workshop)
- Prometheus : http://localhost:9090
- Dashboard Docker / cAdvisor : Dashboard ID 14282