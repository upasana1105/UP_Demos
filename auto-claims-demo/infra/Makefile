GOOGLE_CLOUD_PROJECT ?= $(shell gcloud config get-value project)
PROJECT_NUMBER ?= $(shell gcloud projects describe ${GOOGLE_CLOUD_PROJECT} --format="value(projectNumber)")
GOOGLE_CLOUD_LOCATION ?= $(shell gcloud config get-value compute/region)

.PHONY: infra lb base

infra:
	@echo "Setting up foundation..."
	export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT} ;\
	export GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION} ;\
	python3 setup.py

lb:
	@echo "Setting up Global Application Load Balancer..."
	export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT} ;\
	export GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION} ;\
	python3 setup_lb.py

base:
	@echo "Building auto-claims-ai-service-base image..."
	export REGION=${GOOGLE_CLOUD_LOCATION} ;\
	export PROJECT_ID=${GOOGLE_CLOUD_PROJECT} ;\
	export PROJECT_NUMBER=${PROJECT_NUMBER} ;\
	export LOCATION=${GOOGLE_CLOUD_LOCATION} ;\
	gcloud builds submit base/ --config=base/base.yaml --region=${GOOGLE_CLOUD_LOCATION} --substitutions=_REGION=${GOOGLE_CLOUD_LOCATION}
	@echo "\n=================================================================================="
	@echo "IMPORTANT: Don't forget to update the base image path in ai-service/Dockerfile"
	@echo "to use the correct project ID before running 'make ai-service'!"
	@echo "==================================================================================\n"

