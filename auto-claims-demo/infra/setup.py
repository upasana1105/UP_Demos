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

import os
import subprocess
import sys

def run_command(command, ignore_errors=False):
    """Run a shell command and print its output."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if result.returncode != 0 and not ignore_errors:
        print(f"Error executing: {command}")
        print(result.stderr)
        sys.exit(1)
    return result.stdout.strip()

def setup_infrastructure():
    # Configuration
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        project_id = run_command("gcloud config get-value project", ignore_errors=True)
    if not project_id:
        print("Error: Could not determine GOOGLE_CLOUD_PROJECT. Set it as an environment variable or via gcloud config.")
        sys.exit(1)

    location = os.getenv("GOOGLE_CLOUD_LOCATION")
    if not location:
        location = run_command("gcloud config get-value compute/region", ignore_errors=True)
    if not location:
        location = "us-central1"

    service_account_name = "auto-claims-sa"
    service_account_email = f"{service_account_name}@{project_id}.iam.gserviceaccount.com"

    # Define resource names
    buckets = [
        f"gs://{project_id}-auto-claims",
        f"gs://{project_id}-agent-logs"
    ]

    print(f"Using Project ID: {project_id}")
    print(f"Using Location: {location}")

    # 1. Enable APIs
    print("\n--- Enabling necessary APIs ---")
    apis = [
        "aiplatform.googleapis.com",
        "iam.googleapis.com",
        "serviceusage.googleapis.com",
        "storage.googleapis.com",
        "cloudresourcemanager.googleapis.com",
        "telemetry.googleapis.com",
        "artifactregistry.googleapis.com",
        "run.googleapis.com",
        "cloudbuild.googleapis.com",
        "cloudtrace.googleapis.com",
        "bigquery.googleapis.com",
        "bigqueryconnection.googleapis.com",
        "secretmanager.googleapis.com",
        "compute.googleapis.com",
        "apphub.googleapis.com",
        "networkservices.googleapis.com",
        "networksecurity.googleapis.com",
        "serviceextensions.googleapis.com",
        "iamconnectors.googleapis.com",
    ]
    print(f"Enabling {len(apis)} APIs...")
    api_list = ' '.join(apis)
    run_command(f"gcloud services enable {api_list} --project {project_id}")

    # 2. Create Service Account
    print("\n--- Creating Service Account ---")
    sa_check = run_command(f"gcloud iam service-accounts describe {service_account_email} --project {project_id}", ignore_errors=True)
    if not sa_check:
        print(f"Creating service account: {service_account_name}...")
        run_command(f'gcloud iam service-accounts create {service_account_name} --display-name="auto-claims-sa" --project {project_id}')
    else:
        print(f"Service account {service_account_name} already exists.")

    # 3. Assign Roles
    print("\n--- Assigning Roles to Service Account ---")
    roles = [
        "roles/aiplatform.user",
        "roles/aiplatform.admin",
        "roles/storage.admin",
        "roles/storage.objectViewer",
        "roles/storage.objectCreator",
        "roles/telemetry.writer",
        "roles/telemetry.tracesWriter",
        "roles/cloudtrace.agent",
        "roles/telemetry.metricsWriter",
        "roles/monitoring.metricWriter",
        "roles/logging.logWriter",
        "roles/serviceusage.serviceUsageConsumer",
        "roles/bigquery.admin",
        "roles/secretmanager.secretAccessor",
        "roles/apphub.editor",
        "roles/artifactregistry.admin",
        "roles/artifactregistry.reader",
        "roles/run.admin",
        "roles/iam.serviceAccountTokenCreator",
        "roles/iam.serviceAccountUser",
        "roles/discoveryengine.agentspaceAdmin",
        "roles/agentregistry.viewer"
    ]
    for role in roles:
        print(f"Adding role {role}...")
        run_command(f"gcloud projects add-iam-policy-binding {project_id} --member=serviceAccount:{service_account_email} --role={role} > /dev/null", ignore_errors=True)

    # 4. Create GCS Buckets
    print("\n--- Creating GCS Buckets ---")
    for bucket in buckets:
        bucket_check = run_command(f"gcloud storage buckets describe {bucket}", ignore_errors=True)
        if not bucket_check:
            print(f"Creating GCS bucket: {bucket} in {location}...")
            run_command(f"gcloud storage buckets create {bucket} --location={location} --uniform-bucket-level-access --public-access-prevention --default-storage-class=STANDARD")
        else:
            print(f"GCS bucket {bucket} already exists.")

    # 5. Create Artifact Registry Repository
    print("\n--- Creating Artifact Registry ---")
    repository_name = "auto-claims"
    repo_check = run_command(f"gcloud artifacts repositories describe {repository_name} --location={location} --project={project_id}", ignore_errors=True)
    if not repo_check:
        print(f"Creating Artifact Registry repository: {repository_name} in {location}...")
        run_command(f'gcloud artifacts repositories create {repository_name} --repository-format=docker --location={location} --project={project_id} --description="Docker repository for auto-claims images"')
    else:
        print(f"Artifact Registry repository {repository_name} already exists.")

    print(f"Granting service account permissions to repository {repository_name}...")
    run_command(f'gcloud artifacts repositories add-iam-policy-binding {repository_name} --location={location} --project={project_id} --member="serviceAccount:{service_account_email}" --role="roles/artifactregistry.repoAdmin"')

    # 6. Create Secrets
    print("\n--- Creating Secrets ---")
    secrets = ["hf-token"]
    for secret in secrets:
        secret_check = run_command(f"gcloud secrets describe {secret} --project {project_id}", ignore_errors=True)
        if not secret_check:
            print(f"Creating Secret Manager secret: {secret}...")
            run_command(f"gcloud secrets create {secret} --replication-policy=automatic --project {project_id}")
            print(f"Adding empty placeholder to {secret}...")
            run_command(f"echo 'REPLACEME' | gcloud secrets versions add {secret} --data-file=- --project {project_id}")
        else:
            print(f"Secret {secret} already exists.")

    # 7. Create BigQuery Dataset
    print("\n--- Creating BigQuery Dataset ---")
    bq_dataset = "adk_agent_analytics"
    bq_check = run_command(f"bq show {project_id}:{bq_dataset}", ignore_errors=True)
    if "Not found" in bq_check or not bq_check:
        print(f"Creating BigQuery dataset: {bq_dataset}...")
        run_command(f"bq mk --location={location} -d {project_id}:{bq_dataset}")
    else:
        print(f"BigQuery dataset {bq_dataset} already exists.")

    # 7.5 Create BigQuery Connection
    print("\n--- Creating BigQuery Connection ---")
    bq_connection_id = "adk-analytics-connection"
    connection_check = run_command(f"bq show --connection --project_id={project_id} --location={location} {bq_connection_id}", ignore_errors=True)
    if "Not found" in connection_check or not connection_check:
        print(f"Creating BigQuery connection: {bq_connection_id}...")
        run_command(f"bq mk --connection --location={location} --project_id={project_id} --connection_type=CLOUD_RESOURCE {bq_connection_id}")
    else:
        print(f"BigQuery connection {bq_connection_id} already exists.")

    print(f"Extracting service account for BigQuery connection {bq_connection_id}...")
    bq_sa_output = run_command(f"bq show --connection --format=json --project_id={project_id} --location={location} {bq_connection_id}", ignore_errors=True)
    import json
    try:
        bq_sa_json = json.loads(bq_sa_output)
        bq_sa = bq_sa_json.get("cloudResource", {}).get("serviceAccountId")
        if bq_sa:
            print(f"Granting BigQuery connection service account {bq_sa} access to the project...")
            run_command(f"gcloud projects add-iam-policy-binding {project_id} --member=serviceAccount:{bq_sa} --role=roles/storage.objectViewer > /dev/null", ignore_errors=True)
            run_command(f"gcloud projects add-iam-policy-binding {project_id} --member=serviceAccount:{bq_sa} --role=roles/storage.objectCreator > /dev/null", ignore_errors=True)
            run_command(f"gcloud projects add-iam-policy-binding {project_id} --member=serviceAccount:{bq_sa} --role=roles/storage.admin > /dev/null", ignore_errors=True)
        else:
            print(f"Warning: Could not parse service account from BigQuery connection {bq_connection_id}.")
    except Exception as e:
        print(f"Warning: Failed to parse BigQuery connection JSON: {e}")

    # 8. Create Cloud Build Worker Pool
    print("\n--- Creating Cloud Build Worker Pool ---")
    pool_name = "auto-claims"
    pool_check = run_command(f"gcloud builds worker-pools describe {pool_name} --region={location} --project={project_id}", ignore_errors=True)
    if not pool_check:
        print(f"Creating Cloud Build worker pool: {pool_name} in {location}...")
        run_command(f"gcloud builds worker-pools create {pool_name} --region={location} --project={project_id} --worker-machine-type=c3-standard-4 --worker-disk-size=500GB")
    else:
        print(f"Cloud Build worker pool {pool_name} already exists.")

    # 9. Create Base Docker Images
    print("\n--- Creating Base Docker Images ---")
    run_command("make base")
    print("\n==================================================================================")
    print("IMPORTANT: Don't forget to update the base image path in ai-service/Dockerfile")
    print("to use the correct project ID before running 'make ai-service'!")
    print("==================================================================================\n")

    # 10. Create Agent Gateway
    print("\n--- Creating Agent Gateway ---")
    gateway_name = "agent-gw-ge"
    gateway_check = run_command(f"gcloud alpha network-services agent-gateways describe {gateway_name} --location={location} --project={project_id}", ignore_errors=True)
    if not gateway_check:
        print(f"Creating Agent Gateway: {gateway_name}...")
        yaml_content = f"""
name: agent-gw-egress
protocols:
  - MCP
googleManaged:
  governedAccessPath: AGENT_TO_ANYWHERE
registries:
  - "//agentregistry.googleapis.com/projects/{{project_id}}/locations/{{location}}"
"""
        import subprocess
        process = subprocess.Popen(
            f"gcloud alpha network-services agent-gateways import {gateway_name} --location={location} --project={project_id}",
            shell=True,
            stdin=subprocess.PIPE,
            text=True
        )
        process.communicate(input=yaml_content.strip())
        if process.returncode != 0:
            print(f"Error creating Agent Gateway {gateway_name}")
            sys.exit(1)
    else:
        print(f"Agent Gateway {gateway_name} already exists.")

    # 11. Create Authz Service Extension
    print("\n--- Creating Authz Service Extension ---")
    extension_name = "agent-gw-egress-iap-authzextension"
    extension_check = run_command(f"gcloud service-extensions authz-extensions describe {extension_name} --location={location} --project={project_id}", ignore_errors=True)
    if not extension_check:
        print(f"Creating Authz Service Extension: {extension_name}...")
        yaml_content = """
name: agent-gw-egress-iap-authzextension
service: iap.googleapis.com
metadata:
 iamEnforcementMode: DRY_RUN
failOpen: true
timeout: "10s"
"""
        yaml_file = "authz-extension.yaml"
        with open(yaml_file, "w") as f:
            f.write(yaml_content.strip())
        
        run_command(f"gcloud service-extensions authz-extensions import {extension_name} --source={yaml_file} --location={location} --project={project_id}")
        os.remove(yaml_file)
    else:
        print(f"Authz Service Extension {extension_name} already exists.")

    # 12. Create Authz Policy
    print("\n--- Creating Authz Policy ---")
    policy_name = "agent-authz-profile"
    policy_check = run_command(f"gcloud beta network-security authz-policies describe {policy_name} --location={location} --project={project_id}", ignore_errors=True)
    if not policy_check:
        print(f"Creating Authz Policy: {policy_name}...")
        yaml_content = f"""
name: agent-authz-profile
target:
  resources:
  - "//networkservices.googleapis.com/projects/{project_id}/locations/{location}/agentGateways/agent-gw-ge"
policyProfile: REQUEST_AUTHZ

action: CUSTOM
customProvider:
  authzExtension:
    resources:
    - "projects/{project_id}/locations/{location}/authzExtensions/agent-gw-egress-iap-authzextension"
"""
        yaml_file = "authz-profile.yaml"
        with open(yaml_file, "w") as f:
            f.write(yaml_content.strip())
        
        run_command(f"gcloud beta network-security authz-policies import {policy_name} --source={yaml_file} --location={location} --project={project_id}")
        os.remove(yaml_file)
    else:
        print(f"Authz Policy {policy_name} already exists.")

    # 13. Create Agent Registry Service
    print("\n--- Creating Agent Registry Service ---")
    service_id = "all-apis"
    service_check = run_command(f"gcloud alpha agent-registry services describe {service_id} --location={location} --project={project_id}", ignore_errors=True)
    if not service_check:
        print(f"Creating Agent Registry service: {service_id}...")
        urls = [
            "https://agentregistry.googleapis.com",
            "https://agentregistry.mtls.googleapis.com",
            "https://aiplatform.googleapis.com/",
            "https://cloudresourcemanager.googleapis.com",
            "https://cloudresourcemanager.mtls.googleapis.com",
            "https://logging.googleapis.com",
            "https://logging.mtls.googleapis.com",
            "https://logging.us-central1.rep.googleapis.com",
            "https://monitoring.googleapis.com",
            "https://monitoring.mtls.googleapis.com",
            "https://oauth2.googleapis.com",
            "https://oauth2.mtls.googleapis.com",
            "https://telemetry.googleapis.com",
            "https://telemetry.mtls.googleapis.com",
            "https://telemetry.us-central1.rep.googleapis.com",
            "https://trace.googleapis.com",
            "https://trace.mtls.googleapis.com",
            "https://us-central1-agentregistry.googleapis.com",
            "https://us-central1-agentregistry.mtls.googleapis.com",
            "https://us-central1-cloudresourcemanager.googleapis.com",
            "https://us-central1-cloudresourcemanager.mtls.googleapis.com",
            "https://us-central1-logging.googleapis.com",
            "https://us-central1-logging.mtls.googleapis.com",
            "https://us-central1-monitoring.googleapis.com",
            "https://us-central1-monitoring.mtls.googleapis.com",
            "https://us-central1-oauth2.googleapis.com",
            "https://us-central1-oauth2.mtls.googleapis.com",
            "https://us-central1-telemetry.googleapis.com",
            "https://us-central1-telemetry.mtls.googleapis.com",
            "https://us-central1-trace.googleapis.com",
            "https://us-central1-trace.mtls.googleapis.com",
            "https://iap.googleapis.com",
            "https://iap.mtls.googleapis.com",
            "https://us-central1-iap.googleapis.com",
            "https://us-central1-iap.mtls.googleapis.com"
        ]
        import json
        interfaces = [{"url": url, "protocolBinding": "HTTP_JSON"} for url in urls]
        interfaces_json = json.dumps(interfaces)

        run_command(f'gcloud alpha agent-registry services create {service_id} --location={location} --project={project_id} --display-name="All APIs Consolidated" --description="consolidated APIs to allow Agent Engine to function." --interfaces=\'{interfaces_json}\'')
    else:
        print(f"Agent Registry service {service_id} already exists.")

    print("\nInfrastructure setup script completed successfully.")

if __name__ == "__main__":
    setup_infrastructure()
