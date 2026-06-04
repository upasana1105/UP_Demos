# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# FROM python:3.12-slim-bookworm
# COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies required by OpenCV and Ultralytics
# RUN apt-get update && apt-get install -y \
#     libgl1 \
#     libglib2.0-0 \
#     gcc \
#    && rm -rf /var/lib/apt/lists/*
# --------------------------- USE BASE IMAGE --------------------------------
FROM REPLACE-LOCATION-docker.pkg.dev/REPLACE-PROJECT-ID/auto-claims/auto-claims-ai-service-base:latest
LABEL org.opencontainers.image.url='https://github.com/srinandan/auto-claims-demo/ai-service' \
    org.opencontainers.image.documentation='https://github.com/srinandan/auto-claims-demo/ai-service' \
    org.opencontainers.image.source='https://github.com/srinandan/auto-claims-demo/ai-service' \
    org.opencontainers.image.vendor='Google LLC' \
    org.opencontainers.image.licenses='Apache-2.0'

WORKDIR /code

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies first (Cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Copy source code and install project (Fast layer)
COPY *.py ./
RUN uv sync --frozen

ARG COMMIT_SHA=""
ENV COMMIT_SHA=${COMMIT_SHA}

ARG AGENT_VERSION=0.0.0
ENV AGENT_VERSION=${AGENT_VERSION}

ENV PORT=8080
ENV OTEL_SERVICE_NAME=auto-claims-ai-service
ENV ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false
ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
ENV OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT

EXPOSE 8080

CMD ["uv", "run", "main.py"]
