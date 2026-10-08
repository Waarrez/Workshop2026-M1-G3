# Sentinel-X — Infrastructure & Monitoring

Ce répertoire contient la configuration complète de l'infrastructure Docker pour le projet SENTINEL-X (Workshop EPSI M1 2026, équipe G3).

## Architecture des services

| Service | Port externe | Port interne | Rôle |
| :--- | :--- | :--- | :--- |
| **mosquitto** | 8883 (TLS) · 127.0.0.1:9001 (WS) | 8883 · 9001 | Broker MQTT sécurisé (MQTTS + WebSocket) |
| **api** | 127.0.0.1:8000 | 8000 | API FastAPI (REST + WebSocket `/ws`) |
| **db** | — (réseau interne) | 5432 | Base PostgreSQL, aucun port publié |
| **interface** | 8081 | 80 | Dashboard de supervision (nginx) |
| **grafana** | 127.0.0.1:3000 | 3000 | Tableaux de bord & métriques |
| **prometheus** | 127.0.0.1:9090 | 9090 | Collecteur de séries temporelles |
| **cadvisor** | — (réseau interne) | 8080 | Métriques des conteneurs pour Prometheus |

> Grafana et Prometheus sont volontairement restreints à `127.0.0.1` (non accessibles depuis le reste du hotspot) suite à un audit Nmap ayant révélé leur exposition par défaut. Ne pas republier ces ports sans raison documentée.

## Réseau & sécurité

- Accès ESP8266 : IP du hotspot `192.168.137.1`, port MQTTS `8883`, règle de pare-feu Windows restreignant ce port au sous-réseau `192.168.137.0/24`.
- Authentification MQTT : 3 comptes avec ACL différenciées (`esp8266`, `backend`, `dashboard`) — voir `mosquitto/acl.conf`.
- Chiffrement : TLS 1.2/1.3 sur le broker MQTT (certificat `mosquitto/certs/`). **Le dashboard et l'API ne sont pas servis en HTTPS actuellement** — limite connue, à traiter avant le pentest croisé.
- Réseaux Docker internes : `mqtt` sur `172.28.1.0/24`, `db` sur `172.28.2.0/24` (réseau `internal: true`, aucune route sortante — PostgreSQL n'est joignable que par les conteneurs du même réseau).
- Aucun secret, mot de passe ou clé privée n'est présent dans ce dépôt. Toutes les valeurs sensibles passent par `.env` (non committé, voir `.env.example`) ou par `docker-compose.override.yml` (également non committé).

## Démarrage rapide

```bash
# 1. Copier le modèle d'environnement et renseigner les valeurs (mots de passe MQTT, DB, Grafana...)
cp .env.example .env

# 2. Démarrer l'ensemble de la stack
docker compose up -d --build

# 3. Vérifier que tous les services sont healthy
docker compose ps
```

## Monitoring & supervision

- Grafana : http://127.0.0.1:3000 — identifiants définis dans `.env` (`GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD`).
- Prometheus : http://127.0.0.1:9090
- Dashboard cAdvisor dans Grafana : import du dashboard ID `14282`.
- Dashboard de supervision SENTINEL-X : http://localhost:8081

## Structure du dépôt

```
api/        API FastAPI, bridge MQTT, modèles Pydantic
camera/     Script de vision par ordinateur
infra/      docker-compose.yml, configuration mosquitto, certificats
interface/  Dashboard web (nginx)
```

## Limites connues

- Dashboard/API non chiffrés (HTTP, pas HTTPS) — à corriger ou à documenter comme limite assumée.
- API sans authentification par jeton — accès ouvert à quiconque sur le hotspot.
- Mots de passe de test partagés entre comptes en développement — à individualiser avant la finale.