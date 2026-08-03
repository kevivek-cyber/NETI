# One image, one service: build the exam client, then serve it from the
# same FastAPI process that exposes the API. Same origin, no CORS.
#
# Doubles as the offline centre-node image described in
# docs/ARCHITECTURE.md § Deployment.

FROM node:20-alpine AS web
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY --from=web /build/dist frontend/dist

ENV PYTHONPATH=/app/backend \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
