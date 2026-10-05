# --- Étape 1 : installation des dépendances ---
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Étape 2 : image finale ---
FROM python:3.12-slim
WORKDIR /api

COPY --from=builder /install /usr/local
RUN useradd --create-home appuser
COPY . .

USER appuser
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
