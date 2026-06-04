GOOGLE_CLOUD_PROJECT ?= $(shell gcloud config get-value project)
PROJECT_NUMBER ?= $(shell gcloud projects describe ${GOOGLE_CLOUD_PROJECT} --format="value(projectNumber)")
GOOGLE_CLOUD_LOCATION ?= $(shell gcloud config get-value compute/region)
ifeq ($(GOOGLE_CLOUD_LOCATION),)
GOOGLE_CLOUD_LOCATION := us-central1
endif

_COMMIT_SHA ?= $(shell echo | find app pyproject.toml uv.lock -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -c 1-10)
OTEL_EXPORTER_OTLP_ENDPOINT=https://telemetry.googleapis.com
BQ_ANALYTICS_DATASET_LOCATION="US"
PORT ?= 8083
REASONING_ENGINE_ID ?= 109405805010223104
SHARED_AGENT_ENGINE_ID ?= 3064462601669836800
AGENT_GATEWAY ?= agent-gateway

.PHONY: local deploy setup-iam

local: local-repair-shop-agent

local-repair-shop-agent:
	export _COMMIT_SHA=${_COMMIT_SHA} ;\
	export REGION=${GOOGLE_CLOUD_LOCATION} ;\
	export PROJECT_ID=${GOOGLE_CLOUD_PROJECT} ;\
	export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT} ;\
	export GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION} ;\
	export BQ_ANALYTICS_GCS_BUCKET=${GOOGLE_CLOUD_PROJECT} ;\
	export BQ_ANALYTICS_CONNECTION_ID=${GOOGLE_CLOUD_PROJECT} ;\
	export PROJECT_NUMBER=${PROJECT_NUMBER} ;\
	export LOGS_BUCKET_NAME=${GOOGLE_CLOUD_PROJECT} ;\
	export OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT} ;\
	export PORT=${PORT} ;\
	uv run uvicorn app.fast_api_app:app --host localhost --port ${PORT} --reload

lint:
	uv run codespell
	uv run ruff check . --diff
	uv run ruff format .
	uv run mypy .

deploy:
	export _COMMIT_SHA=${_COMMIT_SHA} ;\
	export REGION=${GOOGLE_CLOUD_LOCATION} ;\
	export PROJECT_ID=${GOOGLE_CLOUD_PROJECT} ;\
	export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT} ;\
	export GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION} ;\
	export BQ_ANALYTICS_GCS_BUCKET=${GOOGLE_CLOUD_PROJECT} ;\
	export BQ_ANALYTICS_CONNECTION_ID=${GOOGLE_CLOUD_PROJECT} ;\
	export BQ_ANALYTICS_DATASET_LOCATION=${BQ_ANALYTICS_DATASET_LOCATION} ;\
	export PROJECT_NUMBER=${PROJECT_NUMBER} ;\
	export LOGS_BUCKET_NAME=${GOOGLE_CLOUD_PROJECT} ;\
	export OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT} ;\
	export REASONING_ENGINE_ID=${REASONING_ENGINE_ID} ;\
	export SHARED_AGENT_ENGINE_ID=${SHARED_AGENT_ENGINE_ID} ;\
	export AGENT_GATEWAY=${AGENT_GATEWAY} ;\
	.venv/bin/python -m app.app_utils.deploy \
		--source-packages=./app \
		--entrypoint-module=app.agent_engine_app \
		--entrypoint-object=agent_engine \
		--location=${GOOGLE_CLOUD_LOCATION} \
		--agent-identity \
		--agent-gateway=${AGENT_GATEWAY} \
		--set-env-vars=GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION},GOOGLE_API_PREVENT_AGENT_TOKEN_SHARING_FOR_GCP_SERVICES=false,OTEL_SERVICE_NAME=auto-claims-repair-shop-agent,OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true,SHARED_AGENT_ENGINE_ID=${SHARED_AGENT_ENGINE_ID},REASONING_ENGINE_ID=${REASONING_ENGINE_ID},GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true,BQ_ANALYTICS_DATASET_LOCATION=${BQ_ANALYTICS_DATASET_LOCATION} \
		--requirements-file=app/app_utils/.requirements.txt


setup-iam:
	@if [ -f deployment_metadata.json ]; then \
		PRINCIPAL=$$(jq -r '.principal' deployment_metadata.json) ;\
		echo "Binding IAM role 'roles/agentregistry.viewer' to principal $${PRINCIPAL} on project level..." ;\
		gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
			--member="$${PRINCIPAL}" \
			--role="roles/agentregistry.viewer" ;\
		gcloud beta iap web add-iam-policy-binding \
			--resource-type=iap_web \
			--project=${GOOGLE_CLOUD_PROJECT} \
			--member="$${PRINCIPAL}" \
			--role="roles/iap.egressor" ;\
		.venv/bin/python iam.py ;\
	else \
		echo "deployment_metadata.json not found. Run 'make deploy' first." ;\
	fi


