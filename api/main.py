from factory import get_fastapi

app = get_fastapi()

@app.get("/health")
def health():
    return {"status": "ok"}
