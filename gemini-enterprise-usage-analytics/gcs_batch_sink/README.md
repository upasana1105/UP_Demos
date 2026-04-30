# GCS Batched Logs analytical stack

This module establishes unified reporting from Google Cloud Logging sinks streaming **directly to Google Cloud Storage (GCS)**. Because Cloud Logging batches log events into hourly structured archives on GCS, this setup lets you query those files immediately natively within BigQuery via External Tables.

## Why this pattern?

Raw logs exported via Cloud Logging GCS destinations present nested fields in `camelCase` format, making traditional structural definitions difficult to keep unified. To securely parse unpredictable payloads, this structure relies on BigQuery native `JSON` mapping combined with automated data views!

## Contents

- **`gcs_transformed.sql`**: SQL schema declaring the GCS External Table interface along with dynamic parsed views.
- **`deploy_gcs_pipeline.sh`**: Shell command to build datasets and view logic reliably via standard configuration flags.

## Setup Steps

Assign external parameters and compile offline sequentially:

```bash
export PROJECT_ID="uppdemos"
export GCS_DATASET="ge_gcs_batch_logs"

./deploy_gcs_pipeline.sh
```

After spinning up, you will be prepared to query records sequentially using:

```sql
SELECT methodName, COUNT(*) 
FROM `uppdemos.ge_gcs_batch_logs.gcs_ge_logs`
GROUP BY methodName;
```
