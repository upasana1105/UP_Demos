# Gemini Enterprise & NotebookLM Usage Analytics

This directory contains tools to extract observability, user behaviors, and interaction metadata from Gemini Enterprise and NotebookLM products on Google Cloud Platform.

## Project Contents

- **`enable_audit_logging.sh`**: Enables audit logs globally for the designated Gemini Enterprise App ID.
- **`bigquery_realitime_sink/`**: Real-time BigQuery schema creation and sink binding scripts.
- **`gcs_batch_sink/`**: External BigQuery tables bound to Cloud Storage batch folders.

## Setup Instructions

Before setting up the analytics pipeline, ensure you have logged in to the Google Cloud CLI:

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project uppdemos
```

Once authenticated:

1. **Run the Global Audit Log Activator:**
   ```bash
   export PROJECT_ID="uppdemos"
   export APP_ID="gemini-enterprise-gm_1771086459519"
   ./enable_audit_logging.sh
   ```

2. **Run the Interactive Pipeline Wizard:**
   ```bash
   cd bigquery_realitime_sink
   ./interactive_runner.sh
   ```

Enjoy your usage analytics dashboards!
