-- 1. Create Placeholder Tables If They Do Not Exist
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}search.discoveryengine_googleapis_com_gemini_enterprise_user_activity` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}search.discoveryengine_googleapis_com_gemini_enterprise_user_activity_legacy` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}assist.discoveryengine_googleapis_com_gemini_enterprise_user_activity` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}streamassist.discoveryengine_googleapis_com_gemini_enterprise_user_activity` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}answerquery.discoveryengine_googleapis_com_gemini_enterprise_user_activity` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}createengine.discoveryengine_googleapis_com_gemini_enterprise_user_activity` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}updateengine.discoveryengine_googleapis_com_gemini_enterprise_user_activity` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}setiampolicy.discoveryengine_googleapis_com_gemini_enterprise_user_activity` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}createagent.discoveryengine_googleapis_com_gemini_enterprise_user_activity` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}updateagent.discoveryengine_googleapis_com_gemini_enterprise_user_activity` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}createagentrequest.discoveryengine_googleapis_com_gemini_enterprise_user_activity` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}generategroundedcontent.discoveryengine_googleapis_com_gemini_enterprise_user_activity` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}updatedataconnector.discoveryengine_googleapis_com_gemini_enterprise_user_activity` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}addcontextfile.discoveryengine_googleapis_com_gemini_enterprise_user_activity` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}uploadsessionfile.discoveryengine_googleapis_com_gemini_enterprise_user_activity` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${GE_DATASET_PREFIX}writeuserevent.discoveryengine_googleapis_com_gemini_enterprise_user_activity` (timestamp TIMESTAMP, jsonPayload JSON, insertId STRING) PARTITION BY DATE(timestamp);


CREATE OR REPLACE VIEW `${PROJECT_ID}.${GE_TRANSFORMED_DATASET}.ge_logs` AS

-- CTE 1: Gathers all raw log tables, bridging both the new active table and the legacy history table seamlessly
WITH base_logs AS (
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}search.discoveryengine_googleapis_com_gemini_enterprise_user_activity` UNION ALL
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}search.discoveryengine_googleapis_com_gemini_enterprise_user_activity_legacy` UNION ALL
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}assist.discoveryengine_googleapis_com_gemini_enterprise_user_activity` UNION ALL
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}streamassist.discoveryengine_googleapis_com_gemini_enterprise_user_activity` UNION ALL
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}answerquery.discoveryengine_googleapis_com_gemini_enterprise_user_activity` UNION ALL
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}createengine.discoveryengine_googleapis_com_gemini_enterprise_user_activity` UNION ALL
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}updateengine.discoveryengine_googleapis_com_gemini_enterprise_user_activity` UNION ALL
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}setiampolicy.discoveryengine_googleapis_com_gemini_enterprise_user_activity` UNION ALL
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}createagent.discoveryengine_googleapis_com_gemini_enterprise_user_activity` UNION ALL
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}updateagent.discoveryengine_googleapis_com_gemini_enterprise_user_activity` UNION ALL
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}createagentrequest.discoveryengine_googleapis_com_gemini_enterprise_user_activity` UNION ALL
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}generategroundedcontent.discoveryengine_googleapis_com_gemini_enterprise_user_activity` UNION ALL
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}updatedataconnector.discoveryengine_googleapis_com_gemini_enterprise_user_activity` UNION ALL
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}addcontextfile.discoveryengine_googleapis_com_gemini_enterprise_user_activity` UNION ALL
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}uploadsessionfile.discoveryengine_googleapis_com_gemini_enterprise_user_activity` UNION ALL
  SELECT TO_JSON_STRING(jsonPayload) as json_str, timestamp FROM `${PROJECT_ID}.${GE_DATASET_PREFIX}writeuserevent.discoveryengine_googleapis_com_gemini_enterprise_user_activity`
),

-- CTE 2: Engine to Name mappings
agent_mappings AS (
  SELECT DISTINCT
    COALESCE(
      REGEXP_EXTRACT(JSON_VALUE(json_str, '$.request.name'), r'/engines/([^/]+)'),
      REGEXP_EXTRACT(JSON_VALUE(json_str, '$.response.name'), r'/engines/([^/]+)'),
      REGEXP_EXTRACT(JSON_VALUE(json_str, '$.request.parent'), r'/engines/([^/]+)')
    ) as engine_id,
    COALESCE(
      JSON_VALUE(json_str, '$.request.agent.displayname'),
      JSON_VALUE(json_str, '$.request.agent.displayName'),
      JSON_VALUE(json_str, '$.response.displayname'),
      JSON_VALUE(json_str, '$.response.displayName')
    ) as agent_display_name
  FROM base_logs
  WHERE COALESCE(
    JSON_VALUE(json_str, '$.logmetadata.methodname'),
    JSON_VALUE(json_str, '$.logMetadata.methodName')
  ) = 'CreateAgent'
),

-- CTE 3: Normalization and Extraction
flattened_logs AS (
  SELECT
    SAFE.PARSE_JSON(JSON_QUERY(json_str, '$.request')) AS request,
    SAFE.PARSE_JSON(JSON_QUERY(json_str, '$.response')) AS response,
    
    COALESCE(
      JSON_VALUE(json_str, '$.logmetadata.servicelabel'),
      JSON_VALUE(json_str, '$.logMetadata.serviceLabel')
    ) AS serviceLabel,
    
    COALESCE(
      JSON_VALUE(json_str, '$.logmetadata.methodname'),
      JSON_VALUE(json_str, '$.logMetadata.methodName')
    ) AS methodName,
    
    COALESCE(
      JSON_VALUE(json_str, '$.useriamprincipal'),
      JSON_VALUE(json_str, '$.userIamPrincipal')
    ) AS userIamPrincipal,
    
    COALESCE(
      JSON_VALUE(json_str, '$.request.query.parts[0].text'),
      JSON_VALUE(json_str, '$.request.query'),
      JSON_VALUE(json_str, '$.request.userEvent.eventType')
    ) AS userQuery,
    
    COALESCE(
      JSON_VALUE(json_str, '$.servicetextreply'),
      JSON_VALUE(json_str, '$.serviceTextReply')
    ) AS serviceTextReply,
    
    COALESCE(
      JSON_VALUE(json_str, '$.response.assisttoken'),
      JSON_VALUE(json_str, '$.response.attributiontoken'),
      JSON_VALUE(json_str, '$.response.assistToken')
    ) AS serviceAttributionToken,
    
    COALESCE(
      JSON_VALUE(json_str, '$.logmetadata.servicename'),
      JSON_VALUE(json_str, '$.logMetadata.serviceName')
    ) AS serviceName,
    
    COALESCE(
      REGEXP_EXTRACT(JSON_VALUE(json_str, '$.response.answer.name'), r'/sessions/([^/]+)'),
      REGEXP_EXTRACT(JSON_VALUE(json_str, '$.request.userEvent.feedback.conversationInfo.session'), r'/sessions/([^/]+)')
    ) AS session_id,
    
    REGEXP_EXTRACT(JSON_VALUE(json_str, '$.response.answer.name'), r'/assistAnswers/([^/]+)') AS answer_id,
    
    COALESCE(
      REGEXP_EXTRACT(JSON_VALUE(json_str, '$.request.name'), r'/engines/([^/]+)'),
      REGEXP_EXTRACT(JSON_VALUE(json_str, '$.request.parent'), r'/engines/([^/]+)'),
      REGEXP_EXTRACT(JSON_VALUE(json_str, '$.logMetadata.name'), r'/engines/([^/]+)'),
      REGEXP_EXTRACT(JSON_VALUE(json_str, '$.response.name'), r'/engines/([^/]+)')
    ) AS engine_id,
    
    timestamp
  FROM base_logs
)

SELECT
  l.*,
  COALESCE(m.agent_display_name, l.engine_id) as agent_display_name
FROM flattened_logs l
LEFT JOIN agent_mappings m ON l.engine_id = m.engine_id;
