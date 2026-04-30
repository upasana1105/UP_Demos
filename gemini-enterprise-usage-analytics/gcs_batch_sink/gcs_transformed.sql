-- 1. Define the External Table pointing to GCS Audit Logs
-- We explicitly type jsonPayload as JSON to avoid schema inference conflicts across varying method payloads.

CREATE OR REPLACE EXTERNAL TABLE `${PROJECT_ID}.${GCS_DATASET}.raw_audit_logs`
(
  timestamp TIMESTAMP,
  jsonPayload JSON
)
OPTIONS (
  format = 'JSON',
  uris = ['${GCS_URI}/*'],
  ignore_unknown_values = true
);

-- 2. Create the Transformed View unifying the extracted metrics

CREATE OR REPLACE VIEW `${PROJECT_ID}.${GCS_DATASET}.gcs_ge_logs` AS
SELECT
  SAFE.PARSE_JSON(JSON_QUERY(TO_JSON_STRING(jsonPayload), '$.request')) AS request,
  SAFE.PARSE_JSON(JSON_QUERY(TO_JSON_STRING(jsonPayload), '$.response')) AS response,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logMetadata.serviceLabel') AS serviceLabel,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logMetadata.methodName') AS methodName,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.userIamPrincipal') AS userIamPrincipal,
  
  -- Coalesce accessors for varying payload formats
  COALESCE(
    JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.request.query.parts[0].text'),
    JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.request.query')
  ) AS userQuery,
  
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.serviceTextReply') AS serviceTextReply,
  
  COALESCE(
    JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.response.assistToken'),
    JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.response.attributionToken')
  ) AS serviceAttributionToken,
  
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logMetadata.serviceName') AS serviceName,
  REGEXP_EXTRACT(JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.response.answer.name'), r'/sessions/([^/]+)') AS session_id,
  REGEXP_EXTRACT(JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.response.answer.name'), r'/assistAnswers/([^/]+)') AS answer_id,
  
  COALESCE(
    REGEXP_EXTRACT(JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.request.name'), r'/engines/([^/]+)'),
    REGEXP_EXTRACT(JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.request.servingConfig'), r'/engines/([^/]+)')
  ) AS engine_id,
  timestamp
FROM `${PROJECT_ID}.${GCS_DATASET}.raw_audit_logs`;
