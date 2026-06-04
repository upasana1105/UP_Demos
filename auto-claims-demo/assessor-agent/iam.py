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

# pylint: disable=no-member
import json
import logging
import os

import google.auth
import vertexai
from google.cloud import resourcemanager_v3
from google.iam.v1 import iam_policy_pb2, policy_pb2


def set_iam_permissions(metadata_file: str = "deployment_metadata.json"):
    logging.basicConfig(level=logging.INFO)

    if not os.path.exists(metadata_file):
        logging.error(
            f"Metadata file {metadata_file} not found. Run 'make deploy' first."
        )
        return

    with open(metadata_file) as f:
        metadata = json.load(f)

    principal = metadata.get("principal")
    remote_agent_id = metadata.get("remote_agent_engine_id")

    if not principal and remote_agent_id:
        logging.info(
            f"Principal not found in metadata. Fetching for {remote_agent_id}..."
        )
        parts = remote_agent_id.split("/")
        project_id = parts[1]
        location = parts[3]
        vertexai.init(project=project_id, location=location)
        client = vertexai.Client(
            project=project_id,
            location=location,
            http_options={"api_version": "v1beta1"},
        )
        agent = client.agent_engines.get(name=remote_agent_id)
        effective_identity = agent.api_resource.spec.effective_identity
        if effective_identity:
            principal = f"principal://{effective_identity}"

    if not principal:
        logging.error("Principal could not be determined.")
        return

    logging.info(f"Reasoning Engine Principal: {principal}")

    # Extract project_id from principal or metadata
    if remote_agent_id:
        project_id = remote_agent_id.split("/")[1]
    else:
        _, project_id = google.auth.default()

    roles = [
        "roles/aiplatform.user",
        "roles/bigquery.admin",
        "roles/bigquery.user",
        "roles/browser",
        "roles/cloudapiregistry.viewer",
        "roles/cloudtrace.agent",
        "roles/logging.logWriter",
        "roles/monitoring.metricWriter",
        "roles/serviceusage.serviceUsageConsumer",
        "roles/telemetry.metricsWriter",
        "roles/telemetry.tracesWriter",
        "roles/telemetry.writer",
    ]

    logging.info(
        f"Granting {len(roles)} roles to {principal} in project {project_id}..."
    )
    proj_client = resourcemanager_v3.ProjectsClient()
    resource = f"projects/{project_id}"

    policy = proj_client.get_iam_policy(
        request=iam_policy_pb2.GetIamPolicyRequest(resource=resource)
    )

    changed = False
    for role in roles:
        existing_binding = next((b for b in policy.bindings if b.role == role), None)
        if existing_binding:
            if principal not in existing_binding.members:
                existing_binding.members.append(principal)
                changed = True
        else:
            policy.bindings.append(policy_pb2.Binding(role=role, members=[principal]))
            changed = True

    if changed:
        proj_client.set_iam_policy(
            request=iam_policy_pb2.SetIamPolicyRequest(resource=resource, policy=policy)
        )
        logging.info("✅ IAM policy updated successfully.")
    else:
        logging.info("All roles already assigned. No changes made.")


if __name__ == "__main__":
    set_iam_permissions()
