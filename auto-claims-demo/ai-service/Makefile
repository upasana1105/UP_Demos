GOOGLE_CLOUD_PROJECT ?= $(shell gcloud config get-value project)
PROJECT_NUMBER ?= $(shell gcloud projects describe ${GOOGLE_CLOUD_PROJECT} --format="value(projectNumber)")
GOOGLE_CLOUD_LOCATION ?= $(shell gcloud config get-value compute/region)
BUCKET_NAME ?= $(shell echo ${GOOGLE_CLOUD_PROJECT}-auto-claims)
_COMMIT_SHA ?= $(shell echo | find . -path ./.venv -prune -o -type f \( -name "*.py" -o -name "uv.lock" \) -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -c 1-10)
ASSESSOR_AGENT_URL ?= http://localhost:8081
PROCESSOR_AGENT_URL ?= http://localhost:8082
REPAIR_SHOP_AGENT_URL ?= http://localhost:8083
PORT ?= 8000
AGENT_ENGINE_ENABLED ?= false

.PHONY: local deploy local-ai-service

local-ai-service: local

local:
	export _COMMIT_SHA=${_COMMIT_SHA} ;\
	export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT} ;\
	export GOOGLE_CLOUD_PROJECT_NUMBER=${PROJECT_NUMBER} ;\
	export GOOGLE_CLOUD_REGION=${GOOGLE_CLOUD_LOCATION} ;\
	export BUCKET_NAME=${BUCKET_NAME} ;\
	export MOCK_MODE=false ;\
	export ASSESSOR_AGENT_URL=${ASSESSOR_AGENT_URL} ;\
	export PROCESSOR_AGENT_URL=${PROCESSOR_AGENT_URL} ;\
	export REPAIR_SHOP_AGENT_URL=${REPAIR_SHOP_AGENT_URL} ;\
	export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT ;\
	export PORT=${PORT} ;\
	export AGENT_ENGINE_ENABLED=${AGENT_ENGINE_ENABLED} ;\
	uv run main.py

deploy:
	sed -i 's/REPLACE-PROJECT-ID/${GOOGLE_CLOUD_PROJECT}/g' Dockerfile
	sed -i 's/REPLACE-LOCATION/${GOOGLE_CLOUD_LOCATION}/g' Dockerfile
	export _COMMIT_SHA=${_COMMIT_SHA} ;\
	export REGION=${GOOGLE_CLOUD_LOCATION} ;\
	export PROJECT_ID=${GOOGLE_CLOUD_PROJECT} ;\
	export PROJECT_NUMBER=${PROJECT_NUMBER} ;\
	gcloud builds submit --config=.cloudbuild/deploy.yaml --region=${GOOGLE_CLOUD_LOCATION} --substitutions=_COMMIT_SHA=${_COMMIT_SHA},_REGION=${GOOGLE_CLOUD_LOCATION} ; \
	RESULT=$$? ; \
	sed -i 's/${GOOGLE_CLOUD_PROJECT}/REPLACE-PROJECT-ID/g' Dockerfile ; \
	sed -i 's/${GOOGLE_CLOUD_LOCATION}/REPLACE-LOCATION/g' Dockerfile ; \
	exit $$RESULT

clean:
	gcloud run services delete auto-claims-$$(basename $$PWD) --region=${GOOGLE_CLOUD_LOCATION} --project=${GOOGLE_CLOUD_PROJECT} --quiet
