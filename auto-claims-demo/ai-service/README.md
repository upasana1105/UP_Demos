[🔙 Back to Main Project README](../README.md)

# Auto Claims AI Service

This service handles image analysis for detecting vehicle damage using **Google Cloud Vertex AI / Gemini** and **YOLOv11**. It orchestrates the claims process by coordinating with specialized agents.

## Tech Stack

-   **Language**: [Python](https://www.python.org/) (v3.11+)
-   **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
-   **AI/ML**:
    -   **Google Cloud Vertex AI** (Gemini Pro Vision) for generative analysis.
    -   **YOLOv11** for object detection (specific damage types).
    -   **Agents**: `claims_agent`, `repair_shop_agent`, `appointment_agent`.
-   **Package Manager**: [uv](https://docs.astral.sh/uv/)

## Prerequisites

-   Python 3.11+
-   `uv` package manager
-   Google Cloud SDK (`gcloud`)

## Configuration

### Environment Variables
The service uses the following environment variables (handled by `Makefile` for local dev):

-   `ASSESSOR_AGENT_URL`: URL of the Assessor Agent (default: `http://localhost:8081`).
-   `PROCESSOR_AGENT_URL`: URL of the Processor Agent (default: `http://localhost:8082`).
-   `GOOGLE_CLOUD_PROJECT`: Project ID for BigQuery analytics and Vertex AI.
-   `GOOGLE_CLOUD_LOCATION`: Google Cloud Region (default: `us-central1`).
-   `GOOGLE_GENAI_USE_VERTEXAI`: Set to `True` to use Vertex AI.
-   `GOOGLE_CLOUD_QUOTA_PROJECT`: Project ID for quota purposes.

### Mock Mode
You can run the service in **Mock Mode** to avoid calling actual Google Cloud APIs.
Set `MOCK_MODE=true` in your environment or `Makefile`.

In Mock Mode:
-   **No GCP calls**: The service will not attempt to contact Vertex AI, Gemini, or GCS.
-   **Hardcoded Responses**: Endpoints will return pre-defined, successful responses (e.g., a "Good" quality score, a specific repair estimate, a list of sample repair shops).
-   **Faster Development**: Useful for frontend/backend development when you don't need real AI inference.

## Setup & Run

### Cloud Deployment

To deploy this service to Cloud Run, you must first build the base image which contains the heavy machine learning dependencies.

1. Build the base image by running:
   ```bash
   make base
   ```
2. Once the base image is built, identify its image URI from the Artifact Registry.
3. Update the `Dockerfile`'s `FROM` instruction to point to this new base image URI.
4. Deploy the actual service by running:
   ```bash
   make deploy
   ```

### Run Locally

```bash
make local
```

This command will:
1.  Set default environment variables.
2.  Start the FastAPI server using `uv` on `http://localhost:8000`.

To run in mock mode:
```bash
MOCK_MODE=true make local-ai-service
```

## API Endpoints

-   `POST /analyze`: Analyzes a single uploaded image for damage.
    -   Inputs: `file` (UploadFile), `photo_id` (Form)
-   `POST /process-claims`: Batch processes images for a claim using a sequential agent.
    -   Inputs: `file_uris` (List[str])
-   `POST /find-repair-shops`: Finds repair shops based on location and damage.
    -   Inputs: `zip_code`, `state`, `make`, `model`, `damage_type`
-   `POST /book-appointment`: Books an appointment with a repair shop via an agent.
    -   Inputs: `session_id`, `message`, `context` (optional)
