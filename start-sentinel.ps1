Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\camera'; py -m uvicorn camera:app --host 0.0.0.0 --port 8001"

cd "$PSScriptRoot\infra"
docker compose up -d