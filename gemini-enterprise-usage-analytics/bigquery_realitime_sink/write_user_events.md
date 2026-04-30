# Write User Events Logs

This document describes all unique types of `WriteUserEvent` logs found in the Private Preview BQ Logs.

## Unique Event Types

The following table lists all unique event types identified by `eventType` and, where applicable, `feedbackType`. Key identifying fields are highlighted in **bold** within the logs.

| Event Type | Description | Full Log |
| :--- | :--- | :--- |
| **Page Visits** | Recorded when a user visits a category page or specific agent space. | <code>{"parent":"projects/1084448453778/locations/global","userEvent":{"agentspaceInfo":{"agentInfo":{"agentId":"677233425077505535"},"agentspacePageType":"agent"},"engine":"projects/1084448453778/locations/global/collections/default_collection/engines/gemini-enterprise-17670338_1767033834650","eventTime":"2026-04-13T13:52:21.461Z","eventType":<b>"view-category-page"</b>,"userInfo":{"userAgent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"},"userPseudoId":"fb9294c7fe7bc41408c1408819e1ddcf"}}</code> |
| **Search** | Recorded when a user performs a search query. | <code>{"parent":"projects/1084448453778/locations/global","userEvent":{"attributionToken":"kQL0EAEKDAjsg6_OBhCqooOyAhIkNjljZDVlMGUtMDAwMC0yOGRhLTg2M2UtNTgyNDI5Y2MyMDdjIgdHRU5FUklDKjiVksUwt7eMLY6-nRXUsp0VwvCeFZvWty2Q97IwmNa3LY_KjjGSyo4xgNKdOIPSnTimrr03r8byNzABUpUBcHJvamVjdHMvMTA4NDQ0ODQ1Mzc3OC9sb2NhdGlvbnMvZ2xvYmFsL2NvbGxlY3Rpb25zL2RlZmF1bHRfY29sbGVjdGlvbi9lbmdpbmVzL2dlbWluaS1lbnRlcnByaXNlLTE3NjcwMzM4XzE3NjcwMzM4MzQ2NTAvc2VydmluZ0NvbmZpZ3MvZGVmYXVsdF9zZWFyY2g","documents":[{"name":"projects/1084448453778/locations/global/collections/default_collection/dataStores/newrag_1768840438762/branches/0/documents/20aedf5eb4c53563d6d86c9aded6187e"},{"name":"projects/1084448453778/locations/global/collections/default_collection/dataStores/notebooks_1770972098876/branches/0/documents/8a989287-59ed-49ad-8fc6-7c075bb9d55d"},{"name":"projects/1084448453778/locations/global/collections/default_collection/dataStores/notebooks_1770972098876/branches/0/documents/fcadd22c-ae0b-4491-900d-bc385c6413a2"},{"name":"projects/1084448453778/locations/global/collections/default_collection/dataStores/notebooks_1770972098876/branches/0/documents/d7005313-09c2-4811-94b2-1f138621eeb7"},{"name":"projects/1084448453778/locations/global/collections/default_collection/dataStores/notebooks_1770972098876/branches/0/documents/bab34c39-71f6-4062-a94e-042e727b11c7"},{"name":"projects/1084448453778/locations/global/collections/default_collection/dataStores/notebooks_1770972098876/branches/0/documents/b7d9b51a-38c0-4e42-b205-64ba892dc01b"},{"name":"projects/1084448453778/locations/global/collections/default_collection/dataStores/notebooks_1770972098876/branches/0/documents/34dc5d4a-c482-48e4-89f4-d342034f1fce"},{"name":"projects/1084448453778/locations/global/collections/default_collection/dataStores/notebooks_1770972098876/branches/0/documents/e460c795-726c-4283-b688-09e213b09886"}],"engine":"projects/1084448453778/locations/global/collections/default_collection/engines/gemini-enterprise-17670338_1767033834650","eventType":<b>"search"</b>,"searchInfo":{"offset":0,"searchQuery":"hi"},"userPseudoId":"fb9294c7fe7bc41408c1408819e1ddcf"},"writeAsync":true}</code> |
| **Click on Like Button** | Recorded when a user provides positive feedback (LIKE). | <code>{"parent":"projects/1084448453778/locations/global","userEvent":{"engine":"projects/1084448453778/locations/global/collections/default_collection/engines/gemini-enterprise-17670338_1767033834650","eventTime":"2026-04-13T13:52:23.992Z","eventType":<b>"add-feedback"</b>,"feedback":{"conversationInfo":{"assistToken":"NMwKDAiy5PPOBhC0wa6RAxIkNjlkY2VlMGYtMDAwMC0yYmM3LTk1OTAtNTgyNDI5YmRjMTU4","session":"collections/default_collection/engines/gemini-enterprise-17670338_1767033834650/sessions/5518543460918369001"},"feedbackSource":"GOOGLE_WEBAPP","feedbackType":<b>"LIKE"</b>,"llmModelVersion":"stable","reasons":["REASON_UNSPECIFIED"]},"userInfo":{"userAgent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"},"userPseudoId":"fb9294c7fe7bc41408c1408819e1ddcf"}}</code> |
| **Click on Dislike Button** | Recorded when a user provides negative feedback (DISLIKE), potentially with comments. | <code>{"parent":"projects/1084448453778/locations/global","userEvent":{"engine":"projects/1084448453778/locations/global/collections/default_collection/engines/gemini-enterprise-17670338_1767033834650","eventTime":"2026-04-13T13:55:01.962Z","eventType":<b>"add-feedback"</b>,"feedback":{"comment":"test comment! 123","conversationInfo":{"assistToken":"NMwKDAiy5PPOBhC0wa6RAxIkNjlkY2VlMGYtMDAwMC0yYmM3LTk1OTAtNTgyNDI5YmRjMTU4","session":"collections/default_collection/engines/gemini-enterprise-17670338_1767033834650/sessions/5518543460918369001"},"feedbackSource":"GOOGLE_WEBAPP","feedbackType":<b>"DISLIKE"</b>,"llmModelVersion":"stable","reasons":["REASON_UNSPECIFIED"]},"userInfo":{"userAgent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"},"userPseudoId":"fb9294c7fe7bc41408c1408819e1ddcf"}}</code> |

## Unique Page Visits Captured

Based on the analysis of `view-category-page` events in the logs, here are the unique pages and agents visited by users:

### General Pages
*   **home**: The main landing page.
*   **notebook-lm**: The NotebookLM interface.
*   **agent_gallery**: The gallery where users can browse available agents.
*   **deep-research**: The Deep Research feature interface.
*   **idea-generation**: The Idea Generation workspace.

### Specific Agent Pages (Applicable only to our Argolis project; Noting it down here for general reference)
The following unique agents have been visited (listed by name when available):
*   **Credit Card Customer Care Expert**
*   **GCP to AWS Return Path Expert**
*   **Movie Information Retriever**
*   **A2A Movie Expert**
*   **Movie Expert**
*   **Calendar Agent**
*   **Story to Python Game Creator**
*   **calculator_agent**
*   **BigQuery Customer Support**
*   **Invoice Question Answering**
*   **Mathematical Calculator**
*   **Home Interior Advisor**
*   **QNA**
*   **Customer Support Assistant**
*   **Infra Helper**
*   **Python Unit Test Generator**
*   **Research And Content Generator**
*   **Unit Converter**
*   **Named Entity Recognizer**
*   **Answer Document Questions**
