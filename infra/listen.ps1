# listen.ps1 - affiche tout ce qui passe sur sentinel/# (compte backend)
# Usage : depuis le dossier infra, .\listen.ps1   (Ctrl+C pour arreter)
$ErrorActionPreference = "Stop"
$cfg = Get-Content .env | ConvertFrom-StringData
docker compose exec mosquitto mosquitto_sub -h localhost -p 8883 `
  --cafile /mosquitto/certs/ca.crt --insecure `
  -u backend -P $cfg.MQTT_BACKEND_PASSWORD -t "sentinel/#" -v
