# simulate-esp.ps1 - simule l'ESP8266 (memes topics que le firmware de DEV)
# Usage : depuis le dossier infra, .\simulate-esp.ps1   (Ctrl+C pour arreter)
# Publie avec le compte esp8266, donc teste aussi l'ACL.
$ErrorActionPreference = "Stop"
$sec = Read-Host "Mot de passe MQTT de esp8266" -AsSecureString
$pw = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))

function Pub($topic, $msg, [switch]$retain) {
  $args2 = @("compose","exec","-T","mosquitto","mosquitto_pub","-h","localhost","-p","8883",
    "--cafile","/mosquitto/certs/ca.crt","--insecure","-u","esp8266","-P",$pw,"-t",$topic,"-m",$msg)
  if ($retain) { $args2 += "-r" }
  docker @args2
  if ($LASTEXITCODE -ne 0) { throw "Publication refusee sur $topic (mot de passe ou ACL ?)" }
}

Pub "sentinel/status" "online" -retain
Write-Host "ESP simule en ligne. Ctrl+C pour arreter."
$i = 0
while ($true) {
  $t = [math]::Round(22 + 3*[math]::Sin($i/6) + (Get-Random -Minimum -5 -Maximum 5)/10, 1)
  $h = [math]::Round(45 + (Get-Random -Minimum -20 -Maximum 20)/10, 1)
  $g = 180 + (Get-Random -Minimum 0 -Maximum 60)
  if ($i % 15 -eq 14) { $g = 750 }           # pic de gaz periodique (> 600 : rouge sur le dashboard)
  $m = if ($i % 10 -ge 7) { "1" } else { "0" }
  Pub "sentinel/sensors/temperature" "$t"
  Pub "sentinel/sensors/humidite" "$h"
  Pub "sentinel/sensors/gaz" "$g"
  Pub "sentinel/sensors/mouvement" $m
  Write-Host ("{0:HH:mm:ss}  T={1}  H={2}  gaz={3}  pir={4}" -f (Get-Date), $t, $h, $g, $m)
  $i++
  Start-Sleep -Seconds 3
}
