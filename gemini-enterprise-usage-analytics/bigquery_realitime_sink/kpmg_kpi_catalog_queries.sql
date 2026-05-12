-- ==============================================================================
-- KPMG KPI Catalog Master Queries (Case: 68431986) - FULL VERSION
-- ==============================================================================
-- This script provides the complete BigQuery SQL logic required to calculate 
-- all trackable metrics from KPMG's KPI Catalog.

-- ------------------------------------------------------------------------------
-- 1. CONVERSATION METRICS (Gemini Chat & User Interactions)
-- ------------------------------------------------------------------------------
SELECT 
  timestamp,
  userIamPrincipal as user,
  session_id,
  
  -- Metric 2: New conversation started
  -- (We track this by identifying the FIRST prompt in a unique session)
  CASE 
    WHEN row_number() OVER(PARTITION BY session_id ORDER BY timestamp ASC) = 1 THEN 1 
    ELSE 0 
  END as is_new_conversation,

  -- Metric 3: # of Prompts/queries submitted
  CASE WHEN methodName IN ('Assist', 'StreamAssist', 'Search', 'AnswerQuery') THEN 1 ELSE 0 END as is_prompt,
  
  -- Metric 11: # of Thumbs Up
  CASE 
    WHEN methodName = 'WriteUserEvent' 
      AND JSON_VALUE(request, '$.userEvent.feedback.feedbackType') = 'LIKE' THEN 1 
    ELSE 0 
  END as is_thumbs_up,
  
  -- Metric 4: # of Thumbs Down
  CASE 
    WHEN methodName = 'WriteUserEvent' 
      AND JSON_VALUE(request, '$.userEvent.feedback.feedbackType') = 'DISLIKE' THEN 1 
    ELSE 0 
  END as is_thumbs_down,
  
  -- Metric 5: Thumbs down details (Comments & Reasons)
  CASE 
    WHEN methodName = 'WriteUserEvent' 
      AND JSON_VALUE(request, '$.userEvent.feedback.feedbackType') = 'DISLIKE' 
      THEN JSON_VALUE(request, '$.userEvent.feedback.comment') 
    ELSE NULL 
  END as thumbs_down_comment,
  
  -- Metric 6: # of File Attachments
  CASE WHEN methodName = 'UploadSessionFile' THEN 1 ELSE 0 END as is_file_attachment,
  
  -- Metric 7: Web search enabled (Y/N)
  COALESCE(
    JSON_VALUE(request, '$.groundingConfig.webSearchEnabled'),
    JSON_VALUE(request, '$.request.groundingConfig.webSearchEnabled'),
    'false'
  ) as web_search_enabled,
  
  -- Metric 10/14: # of Source/Citation Click Throughs
  CASE 
    WHEN methodName = 'WriteUserEvent' 
      AND JSON_VALUE(request, '$.userEvent.eventType') IN ('click-on-source', 'click-on-citation') THEN 1 
    ELSE 0 
  END as is_click_through,

  -- Metric 15: Sources Chosen through toggle (e.g., Enterprise Search, Web)
  JSON_VALUE(request, '$.groundingConfig.dataSources') as data_sources

FROM `uppdemos.ge_transformed.kpmg_standardized_logs`;


-- ------------------------------------------------------------------------------
-- 2. NOTEBOOK LM METRICS (Notebook Creation & Study Artifacts)
-- ------------------------------------------------------------------------------
SELECT 
  timestamp,
  userIamPrincipal as user,
  methodName,
  
  -- Metric 17: Create or Use Current Notebook
  CASE WHEN methodName = 'CreateNotebook' THEN 'Create' ELSE 'Use Current' END as notebook_action,
  
  -- Metric 24: # Audio Overview generated
  CASE WHEN methodName = 'GenerateAudioOverview' THEN 1 ELSE 0 END as is_audio_generated,

  -- Metric 25: # Notes added
  CASE WHEN methodName = 'CreateNote' THEN 1 ELSE 0 END as is_note_added,

  -- Metric 19-22: Generated Artifacts (Study Guides, FAQs, Timelines, Briefing Docs)
  CASE 
    WHEN LOWER(userQuery) LIKE '%study guide%' THEN 'Study Guide'
    WHEN LOWER(userQuery) LIKE '%briefing doc%' THEN 'Briefing Doc'
    WHEN LOWER(userQuery) LIKE '%faq%' THEN 'FAQ'
    WHEN LOWER(userQuery) LIKE '%timeline%' THEN 'Timeline'
    ELSE 'Standard Interaction'
  END as generated_artifact

FROM `uppdemos.nlm_transformed.nlm_logs`;


-- ------------------------------------------------------------------------------
-- 3. SESSION LENGTH CALCULATION (Conversation & NotebookLM)
-- ------------------------------------------------------------------------------
-- Metric 8/27/35: Length of Session (In Minutes)
SELECT 
  session_id,
  userIamPrincipal as user,
  MIN(timestamp) as session_start,
  MAX(timestamp) as session_end,
  TIMESTAMP_DIFF(MAX(timestamp), MIN(timestamp), MINUTE) as session_length_minutes
FROM `uppdemos.ge_transformed.kpmg_standardized_logs`
WHERE session_id IS NOT NULL
GROUP BY 1, 2;


-- ------------------------------------------------------------------------------
-- 4. CUSTOM AGENT METRICS (Bot Usage & Lifecycle)
-- ------------------------------------------------------------------------------
SELECT 
  engine_id as agent_name,
  
  -- Metric 32: Number of personal agents created
  COUNTIF(methodName = 'CreateAgent') as total_agents_created,

  -- Metric 33: # of prompts submitted per Agent
  COUNTIF(methodName IN ('Assist', 'StreamAssist', 'Search')) as total_agent_prompts

FROM `uppdemos.ge_transformed.kpmg_standardized_logs`
WHERE engine_id IS NOT NULL
GROUP BY 1;
