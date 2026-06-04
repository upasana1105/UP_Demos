[🔙 Back to Main Project README](../README.md)

# Repair Shop Agent

ReAct agent with A2A protocol [experimental].
Agent generated with [`googleCloudPlatform/agent-starter-pack`](https://github.com/GoogleCloudPlatform/agent-starter-pack) version `0.36.0`.

## Service Description

The **Repair Shop Agent** is a specialized AI agent responsible for finding suitable repair shops and handling appointment bookings for the final steps of auto claim processing. It interacts with the main AI Service and receives input from other services to orchestrate repairs.

It implements the [A2A (Agent-to-Agent) Protocol](https://a2a-protocol.org/) for standardized communication.

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)
- **jq**: Command-line JSON processor (required for IAM setup automation) - [Install](https://jqlang.github.io/jq/download/)
- **make**: Build automation tool (pre-installed on most Unix-based systems)

## Quick Start

Install required packages and launch the local development environment:

```bash
make install && make playground
```

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `make install`       | Install dependencies using uv                                                               |
| `make playground`    | Launch local development environment                                                        |
| `make deploy`         | Deploy agent to Cloud Run                                                                   |
| `make setup-iam`      | Set up IAM permissions for the reasoning engine principal and IAP egressor policy for Agent Registry |
| `make local-repair-shop-agent` | Launch local development server on port 8083                                   |

For full command options and usage, refer to the [Makefile](Makefile).

## Deployment

```bash
gcloud config set project <your-project-id>
make deploy
make setup-iam
```
