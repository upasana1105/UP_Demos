CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${NLM_DATASET_PREFIX}createnotebook.discoveryengine_googleapis_com_gemini_enterprise_user_activity` PARTITION BY DATE(timestamp) AS SELECT * FROM `${PROJECT_ID}.${NLM_DATASET_PREFIX}createnotebook.discoveryengine_googleapis_com_gemini_enterprise_user_activity` LIMIT 0;
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${NLM_DATASET_PREFIX}sharenotebook.discoveryengine_googleapis_com_gemini_enterprise_user_activity` PARTITION BY DATE(timestamp) AS SELECT * FROM `${PROJECT_ID}.${NLM_DATASET_PREFIX}createnotebook.discoveryengine_googleapis_com_gemini_enterprise_user_activity` LIMIT 0;
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${NLM_DATASET_PREFIX}batchdeletenotebooks.discoveryengine_googleapis_com_gemini_enterprise_user_activity` PARTITION BY DATE(timestamp) AS SELECT * FROM `${PROJECT_ID}.${NLM_DATASET_PREFIX}createnotebook.discoveryengine_googleapis_com_gemini_enterprise_user_activity` LIMIT 0;
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${NLM_DATASET_PREFIX}getnotebook.discoveryengine_googleapis_com_gemini_enterprise_user_activity` PARTITION BY DATE(timestamp) AS SELECT * FROM `${PROJECT_ID}.${NLM_DATASET_PREFIX}createnotebook.discoveryengine_googleapis_com_gemini_enterprise_user_activity` LIMIT 0;
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${NLM_DATASET_PREFIX}interactsources.discoveryengine_googleapis_com_gemini_enterprise_user_activity` PARTITION BY DATE(timestamp) AS SELECT * FROM `${PROJECT_ID}.${NLM_DATASET_PREFIX}createnotebook.discoveryengine_googleapis_com_gemini_enterprise_user_activity` LIMIT 0;
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${NLM_DATASET_PREFIX}generatefreeformstreamed.discoveryengine_googleapis_com_gemini_enterprise_user_activity` PARTITION BY DATE(timestamp) AS SELECT * FROM `${PROJECT_ID}.${NLM_DATASET_PREFIX}createnotebook.discoveryengine_googleapis_com_gemini_enterprise_user_activity` LIMIT 0;

CREATE OR REPLACE VIEW `${PROJECT_ID}.${NLM_TRANSFORMED_DATASET}.nlm_logs` AS

SELECT
  JSON_QUERY(TO_JSON_STRING(jsonPayload), '$.request') AS request,
  JSON_QUERY(TO_JSON_STRING(jsonPayload), '$.response') AS response,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.servicelabel') AS serviceLabel,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.methodname') AS methodName,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.useriamprincipal') AS userIamPrincipal,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.request.userquery') AS userQuery,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.servicetextreply') AS serviceTextReply,
  CAST(NULL AS STRING) AS serviceAttributionToken,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.servicename') AS serviceName,
  timestamp
FROM `${PROJECT_ID}.${NLM_DATASET_PREFIX}createnotebook.discoveryengine_googleapis_com_gemini_enterprise_user_activity`

UNION ALL

SELECT
  JSON_QUERY(TO_JSON_STRING(jsonPayload), '$.request') AS request,
  JSON_QUERY(TO_JSON_STRING(jsonPayload), '$.response') AS response,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.servicelabel') AS serviceLabel,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.methodname') AS methodName,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.useriamprincipal') AS userIamPrincipal,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.request.userquery') AS userQuery,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.servicetextreply') AS serviceTextReply,
  CAST(NULL AS STRING) AS serviceAttributionToken,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.servicename') AS serviceName,
  timestamp
FROM `${PROJECT_ID}.${NLM_DATASET_PREFIX}sharenotebook.discoveryengine_googleapis_com_gemini_enterprise_user_activity`

UNION ALL

SELECT
  JSON_QUERY(TO_JSON_STRING(jsonPayload), '$.request') AS request,
  JSON_QUERY(TO_JSON_STRING(jsonPayload), '$.response') AS response,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.servicelabel') AS serviceLabel,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.methodname') AS methodName,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.useriamprincipal') AS userIamPrincipal,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.request.userquery') AS userQuery,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.servicetextreply') AS serviceTextReply,
  CAST(NULL AS STRING) AS serviceAttributionToken,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.servicename') AS serviceName,
  timestamp
FROM `${PROJECT_ID}.${NLM_DATASET_PREFIX}batchdeletenotebooks.discoveryengine_googleapis_com_gemini_enterprise_user_activity`

UNION ALL

SELECT
  JSON_QUERY(TO_JSON_STRING(jsonPayload), '$.request') AS request,
  JSON_QUERY(TO_JSON_STRING(jsonPayload), '$.response') AS response,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.servicelabel') AS serviceLabel,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.methodname') AS methodName,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.useriamprincipal') AS userIamPrincipal,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.request.userquery') AS userQuery,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.servicetextreply') AS serviceTextReply,
  CAST(NULL AS STRING) AS serviceAttributionToken,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.servicename') AS serviceName,
  timestamp
FROM `${PROJECT_ID}.${NLM_DATASET_PREFIX}getnotebook.discoveryengine_googleapis_com_gemini_enterprise_user_activity`

UNION ALL

SELECT
  JSON_QUERY(TO_JSON_STRING(jsonPayload), '$.request') AS request,
  JSON_QUERY(TO_JSON_STRING(jsonPayload), '$.response') AS response,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.servicelabel') AS serviceLabel,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.methodname') AS methodName,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.useriamprincipal') AS userIamPrincipal,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.request.userquery') AS userQuery,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.servicetextreply') AS serviceTextReply,
  CAST(NULL AS STRING) AS serviceAttributionToken,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.servicename') AS serviceName,
  timestamp
FROM `${PROJECT_ID}.${NLM_DATASET_PREFIX}interactsources.discoveryengine_googleapis_com_gemini_enterprise_user_activity`

UNION ALL

SELECT
  JSON_QUERY(TO_JSON_STRING(jsonPayload), '$.request') AS request,
  JSON_QUERY(TO_JSON_STRING(jsonPayload), '$.response') AS response,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.servicelabel') AS serviceLabel,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.methodname') AS methodName,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.useriamprincipal') AS userIamPrincipal,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.request.userquery') AS userQuery,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.servicetextreply') AS serviceTextReply,
  CAST(NULL AS STRING) AS serviceAttributionToken,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.servicename') AS serviceName,
  timestamp
FROM `${PROJECT_ID}.${NLM_DATASET_PREFIX}generatefreeformstreamed.discoveryengine_googleapis_com_gemini_enterprise_user_activity`;
