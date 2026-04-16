# Stage 1: Build the React Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Final Service (FastAPI + Static Frontend)
FROM python:3.11-slim

WORKDIR /app

# System dependencies for PDF processing if any (optional but good)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Backend Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Manually include missing but required deps
RUN pip install fastapi uvicorn python-multipart python-dotenv google-adk google-cloud-translate importlib-metadata

# Copy Backend Code
COPY . .

# Copy Built Frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8000

ENV PORT=8000
ENV GOOGLE_CLOUD_PROJECT=uppdemos
ENV GOOGLE_CLOUD_LOCATION=us-central1

# Run the backend (which also serves the frontend)
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
