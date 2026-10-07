from fastapi import WebSocket


class Hub:
    def __init__(self):
        self.clients: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.clients.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.clients:
            self.clients.remove(ws)

    async def broadcast(self, message: dict):
        for ws in list(self.clients):       # copie : la liste peut changer pendant l'envoi
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(ws)         # client déconnecté : on le retire