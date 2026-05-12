-- ==============================================================================
-- KPMG Future-Proof Aggregation Layer (Case Insensitive Feedback Fix)
-- ==============================================================================
-- Patches 'is_thumbs_up' and 'is_thumbs_down' to handle case variations between
-- lowercase 'userevent.feedback.feedbacktype' and CamelCase.

CREATE OR REPLACE VIEW `${PROJECT_ID}.${GE_TRANSFORMED_DATASET}.kpmg_standardized_logs` AS
SELECT
  timestamp,
  
  -- 1. Rebranding Shield
  CASE 
    WHEN serviceLabel IN ('AGENTSPACE', 'GEMINI_ENTERPRISE') THEN 'GEMINI_ENTERPRISE'
    ELSE COALESCE(serviceLabel, 'GEMINI_ENTERPRISE')
  END AS serviceLabel,
  
  -- 2. NULL Method Fix
  COALESCE(
    methodName,
    CASE 
      WHEN COALESCE(JSON_VALUE(request, '$.userevent.eventtype'), JSON_VALUE(request, '$.userEvent.eventType')) = 'add-feedback' THEN 'WriteUserEvent_Feedback'
      WHEN COALESCE(JSON_VALUE(request, '$.userevent.eventtype'), JSON_VALUE(request, '$.userEvent.eventType')) IS NOT NULL THEN CONCAT('WriteUserEvent_', COALESCE(JSON_VALUE(request, '$.userevent.eventtype'), JSON_VALUE(request, '$.userEvent.eventType')))
      ELSE 'Background_Or_System_Task'
    END
  ) AS methodName,
  
  -- 3. Inflation Blocker
  CASE 
    WHEN methodName IN ('Assist', 'StreamAssist', 'Search', 'AnswerQuery') THEN TRUE
    ELSE FALSE
  END AS is_true_prompt,
  
  -- 4. Null UserID Handler
  COALESCE(
    userIamPrincipal, 
    'admin-or-system-action'
  ) AS userIamPrincipal,
  
  -- 5. GA Grounding Shield
  CASE 
    WHEN methodName = 'Search' THEN 'true'
    WHEN COALESCE(JSON_VALUE(request, '$.webSearchEnabled'), JSON_VALUE(request, '$.groundingConfig.webSearchEnabled'), JSON_VALUE(request, '$.request.groundingConfig.webSearchEnabled')) = 'true' THEN 'true'
    ELSE 'false'
  END as web_search_enabled,
  
  -- 6. KPMG Feedback Telemetry (Case Insensitive Coalesce Layer!)
  CASE 
    WHEN methodName = 'WriteUserEvent' 
      AND COALESCE(JSON_VALUE(request, '$.userevent.feedback.feedbacktype'), JSON_VALUE(request, '$.userEvent.feedback.feedbackType')) = 'LIKE' THEN 1 
    ELSE 0 
  END as is_thumbs_up,
  
  CASE 
    WHEN methodName = 'WriteUserEvent' 
      AND COALESCE(JSON_VALUE(request, '$.userevent.feedback.feedbacktype'), JSON_VALUE(request, '$.userEvent.feedback.feedbackType')) = 'DISLIKE' THEN 1 
    ELSE 0 
  END as is_thumbs_down,
  
  -- 7. KPMG Feedback Comments Text (Case Insensitive Coalesce Layer!)
  CASE 
    WHEN methodName = 'WriteUserEvent' 
      AND COALESCE(JSON_VALUE(request, '$.userevent.feedback.feedbacktype'), JSON_VALUE(request, '$.userEvent.feedback.feedbackType')) = 'DISLIKE' 
      THEN COALESCE(JSON_VALUE(request, '$.userevent.feedback.comment'), JSON_VALUE(request, '$.userEvent.feedback.comment')) 
    ELSE NULL 
  END as thumbs_down_comment,
  
  -- Standard Columns
  userQuery,
  serviceTextReply,
  session_id,
  engine_id,
  agent_display_name,
  
  answer_id,
  serviceAttributionToken,
  serviceName,
  request,
  response
FROM `${PROJECT_ID}.${GE_TRANSFORMED_DATASET}.ge_logs`;
