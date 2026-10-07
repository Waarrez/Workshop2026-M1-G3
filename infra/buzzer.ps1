# buzzer.ps1 - envoie une commande au buzzer (compte backend)
# Usage : .\buzzer.ps1 on     ou     .\buzzer.ps1 off
param([Parameter(Mandatory=$true)][ValidateSet("on","off")][string]$Etat)
$ErrorActionPreference = "Stop"
$cfg = Get-Content .env | ConvertFrom-StringData
docker compose exec -T mosquitto mosquitto_pub -h localhost -p 8883 `
  --cafile /mosquitto/certs/ca.crt --insecure `
  -u backend -P $cfg.MQTT_BACKEND_PASSWORD -t "sentinel/actuators/buzzer" -m $Etat
Write-Host "Buzzer -> $Etat"
