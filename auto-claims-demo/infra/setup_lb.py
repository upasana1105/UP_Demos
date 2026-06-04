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
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if result.returncode != 0 and not ignore_errors:
        print(f"Error executing: {command}")
        print(result.stderr)
        sys.exit(1)
    return result.stdout.strip()

def setup_lb():
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

    print(f"Using Project ID: {project_id}")
    print(f"Using Location: {location}")

    # 1. Create a global static IP Address
    ip_name = "auto-claims-ip"
    ip_check = run_command(f"gcloud compute addresses describe {ip_name} --global --project {project_id} --format='value(address)'", ignore_errors=True)
    if not ip_check:
        print(f"Creating global static IP Address: {ip_name}...")
        run_command(f"gcloud compute addresses create {ip_name} --global --project {project_id}")
        ip_check = run_command(f"gcloud compute addresses describe {ip_name} --global --project {project_id} --format='value(address)'")
    
    static_ip = ip_check
    print(f"Global IP Address: {static_ip}")

    # 2. Deploy Cloud Endpoints DNS
    domain_name = f"autoclaims.endpoints.{project_id}.cloud.goog"
    print(f"Deploying Cloud Endpoints DNS for domain: {domain_name}")
    
    dns_spec = f"""swagger: "2.0"
info:
  description: "Cloud Endpoints DNS"
  title: "Cloud Endpoints DNS"
  version: "1.0.0"
paths: {{}}
host: "{domain_name}"
x-google-endpoints:
- name: "{domain_name}"
  target: "{static_ip}"
"""
    with open("dns-spec.yaml", "w") as f:
        f.write(dns_spec)
    
    run_command(f"gcloud services enable servicemanagement.googleapis.com --project {project_id}", ignore_errors=True)
    run_command(f"gcloud endpoints services deploy dns-spec.yaml --project {project_id}")

    # 3. Create SSL Certificate
    cert_name = "auto-claims-cert"
    cert_check = run_command(f"gcloud compute ssl-certificates describe {cert_name} --global --project {project_id}", ignore_errors=True)
    if not cert_check:
        print(f"Creating SSL Certificate: {cert_name}...")
        run_command(f"gcloud compute ssl-certificates create {cert_name} --domains={domain_name} --project={project_id} --global")
    else:
        print(f"SSL Certificate {cert_name} already exists.")

    # 4. Create Serverless NEGs
    services = [("auto-claims-frontend", "frontend"), ("auto-claims-backend", "backend")]
    for srv, label in services:
        neg_name = f"auto-claims-{label}-neg"
        neg_check = run_command(f"gcloud compute network-endpoint-groups describe {neg_name} --region={location} --project={project_id}", ignore_errors=True)
        if not neg_check:
            print(f"Creating Serverless NEG for {srv}...")
            # Note: the services must exist first.
            run_command(f"gcloud compute network-endpoint-groups create {neg_name} --region={location} --network-endpoint-type=serverless --cloud-run-service={srv} --project={project_id}", ignore_errors=True)

    # 5. Create Backend Services
    for srv, label in services:
        bs_name = f"auto-claims-{label}-bs"
        bs_check = run_command(f"gcloud compute backend-services describe {bs_name} --global --project={project_id}", ignore_errors=True)
        if not bs_check:
            print(f"Creating Backend Service for {srv}...")
            run_command(f"gcloud compute backend-services create {bs_name} --load-balancing-scheme=EXTERNAL_MANAGED --global --project={project_id}")
            # Attach NEG
            neg_name = f"auto-claims-{label}-neg"
            run_command(f"gcloud compute backend-services add-backend {bs_name} --global --network-endpoint-group={neg_name} --network-endpoint-group-region={location} --project={project_id}", ignore_errors=True)

    # 6. Create URL Map
    url_map_name = "auto-claims-url-map"
    url_map_check = run_command(f"gcloud compute url-maps describe {url_map_name} --project={project_id}", ignore_errors=True)
    if not url_map_check:
        print("Creating URL Map...")
        # Start with default service for frontend
        run_command(f"gcloud compute url-maps create {url_map_name} --default-service=auto-claims-frontend-bs --project={project_id}")
        # Add path matcher for backend
        run_command(f"gcloud compute url-maps add-path-matcher {url_map_name} --default-service=auto-claims-frontend-bs --path-matcher-name=backend-matcher --path-rules='/api/*=auto-claims-backend-bs,/uploads/*=auto-claims-backend-bs' --project={project_id}")
    else:
        print(f"URL Map {url_map_name} already exists.")

    # 7. Create Target HTTPS Proxy
    proxy_name = "auto-claims-https-proxy"
    proxy_check = run_command(f"gcloud compute target-https-proxies describe {proxy_name} --project={project_id}", ignore_errors=True)
    if not proxy_check:
        print("Creating Target HTTPS Proxy...")
        run_command(f"gcloud compute target-https-proxies create {proxy_name} --ssl-certificates={cert_name} --url-map={url_map_name} --project={project_id}")
    else:
        print(f"Target HTTPS Proxy {proxy_name} already exists.")

    # 8. Create Forwarding Rule
    fw_rule_name = "auto-claims-forwarding-rule"
    fw_rule_check = run_command(f"gcloud compute forwarding-rules describe {fw_rule_name} --global --project={project_id}", ignore_errors=True)
    if not fw_rule_check:
        print("Creating Global Forwarding Rule...")
        run_command(f"gcloud compute forwarding-rules create {fw_rule_name} --load-balancing-scheme=EXTERNAL_MANAGED --network-tier=PREMIUM --global --target-https-proxy={proxy_name} --ports=443 --address={ip_name} --project={project_id}")
    else:
        print(f"Forwarding Rule {fw_rule_name} already exists.")

    print("\nLoad Balancer setup completed successfully.")
    print(f"It may take 15-30 minutes for the DNS & SSL certificates to fully propagate.")
    print(f"Your application will be mapped to: https://{domain_name}")
    print("Frontend maps to '/*' and Backend maps to '/api/*' and '/uploads/*'.")

if __name__ == "__main__":
    setup_lb()
