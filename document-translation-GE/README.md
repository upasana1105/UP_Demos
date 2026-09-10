# Financial Document Translation Assistant for Gemini Enterprise (GE)

A production-ready Enterprise Agent built for **Gemini Enterprise (Discovery Engine)** and deployed on **Vertex AI Agent Engine (Reasoning Engine)** using the Google Agent Development Kit (ADK) and the Agent-to-Agent (A2A) protocol.

This agent translates complex financial documents (PDF, DOCX, PPTX), removes attribution watermarks (`NO_ATTRIBUTION`), translates diagrams and in-image text using Gemini Multimodal, conducts financial quality and numerical precision audits, and renders interactive, sandboxed side-by-side dashboards directly inside Gemini Enterprise using **A2UI WebFrameSrcdoc** iframes.

---
![Uploading Screenshot 2026-09-09 at 11.34.42 PM.png…]()

## 🌟 Key Features

1. **Cloud Translation API with Watermark Removal (`NO_ATTRIBUTION`)**:
   - Translates formatted documents preserving tables, layout, font styles, and structure.
   - Enforces `customized_attribution="NO_ATTRIBUTION"` to eliminate the Google "Machine Translated" watermark from all pages.

2. **Multimodal Diagram & Chart Translation**:
   - Detects visual diagrams, charts, and embedded graphics in PDFs and slides.
   - Uses `gemini-3.1-flash-image` to translate text inside graphics and re-inserts localized visuals seamlessly into the output document.

3. ** Financial Quality & Precision Audit**:
   - Automated post-translation quality audit powered by Gemini.
   - Checks for numerical scale accuracy (e.g., Million vs. Billion, Billion vs. German *Milliarden*, preventing 1,000x magnitude errors).
   - Verifies compliance with GAAP/IFRS financial terminology and flags semantic or structural issues with impact ratings (High, Medium, Low).

4. **Interactive A2UI Dashboard & Visual Viewer**:
   - Built on the A2UI v0.8 / v0.9 specification using `WebFrameSrcdoc`.
   - Embeds a branded interactive dashboard directly into the chat stream.
   - Offers multiple comparison modes:
     - **Top-Down Full-Width View**: Displays original and translated pages vertically at 100% width.
     - **Side-by-Side Comparison**: Parallel split view of source and target pages.
     - **Single Document View with Page Navigation**: Flip through individual pages (`< Page 1 of N >`).
     - **Zoom Controls**: Adjust zoom from 50% to 200%.

5. **Direct, Public Clean Document Downloads**:
   - Uploads clean, watermark-free translated documents to Google Cloud Storage (`gs://uppdemos-agent-staging/translations/...`).
   - Serves documents with `Content-Disposition: inline` (or attachment) for direct, one-click downloads without `<AccessDenied>` errors.

6. **Persistent Session Architecture (< 256 KiB Threshold Optimization)**:
   - Page preview images are uploaded to Cloud Storage and referenced via public URLs (`https://storage.googleapis.com/...`), reducing the A2UI JSON payload size from >600 KiB down to **~15 KiB**.
   - Because the payload is well below Discovery Engine's **256 KiB Spanner offload threshold** (`kInlineDataExternalizationThresholdBytes`), it is stored as native `inline_data` rather than a GCS file attachment.
   - **Guarantees that refreshing or reloading the browser page permanently preserves the interactive dashboard without any `application/json+a2ui: Unsupported attachment` errors.**

---

## 🏗️ Architecture

```
                                    +-----------------------------------------+
                                    |     Gemini Enterprise (Discovery Engine)|
                                    |        Chat Interface (UCS Widget)      |
                                    +--------------------+--------------------+
                                                         |
                                      StreamAssist / A2A | Protocol
                                                         v
                                    +--------------------+--------------------+
                                    |  Vertex AI Reasoning Engine / Agent     |
                                    |       (TranslationExecutor)         |
                                    +--------------------+--------------------+
                                                         |
                   +---------------------+---------------+---------------------+
                   |                     |                                     |
                   v                     v                                     v
+------------------+---+  +--------------+----+               +----------------+-----+
| Cloud Translation API|  | Gemini Multimodal |               | Google Cloud Storage |
|  - NO_ATTRIBUTION    |  |  - In-image text  |               |  - Clean translated  |
|  - Layout & tables   |  |  - Financial audit|               |    PDFs & DOCX files |
+----------------------+  +-------------------+               |  - Fast preview JPEGs|
                                                              +----------------------+
```

---

## 📁 Repository Structure

```
document-translation-GE/
├── README.md                           # Comprehensive documentation
├── requirements.txt                    # Python dependencies
├── .env.example                        # Template environment variables
├── sample_doc.pdf                      # Sample 1-page financial test document
├── 5g-edge-computing-value-opportunity.pdf # Sample complex multi-page PDF with diagrams
├── config/
│   ├── _defaults.yaml                  # Global defaults (regions, buckets, timeouts)
│   └── translation_assistant.yaml      # Agent card, skills, and deployment config
├── agents/
│   ├── __init__.py
│   ├── _base/                          # ADK base classes and configuration loaders
│   │   ├── __init__.py
│   │   ├── base_executor.py
│   │   └── config_loader.py
│   └── translation_assistant/          # translation agent implementation
│       ├── __init__.py
│       ├── agent.py                    # ADK agent definition and system prompts
│       ├── components.py               # A2UI message generator & HTML dashboard builder
│       ├── executor.py                 # A2A executor handling turns and UI injection
│       └── tools.py                    # Translation, GCS uploads, image localization, audit
└── scripts/
    ├── deploy.py                       # Deploys agent to Agent Engine & registers in GE
    ├── update_and_patch.py             # Builds, deploys reasoning engine, & patches GE agent card
    ├── setup_agent_auth.py             # Configures Discovery Engine Agent Authorization
    ├── test_local.py                   # Local mock runner for testing execution and A2UI
    └── undeploy.py                     # Undeploys agent from Vertex AI Reasoning Engine
```

---

## 🚀 Deployment Guide

### Prerequisites
- Python 3.11+
- Google Cloud SDK (`gcloud`) authenticated with permissions on your project:
  ```bash
  gcloud auth application-default login
  gcloud config set project YOUR_PROJECT_ID
  ```

### Installation
```bash
cd document-translation-GE
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure Environment
Copy `.env.example` to `.env` and fill in your project values:
```bash
cp .env.example .env
```
Key variables:
- `PROJECT_ID`: Your Google Cloud Project ID (e.g., `uppdemos`).
- `LOCATION`: Vertex AI Region (e.g., `us-central1`).
- `STORAGE_BUCKET`: GCS staging and document hosting bucket (e.g., `gs://uppdemos-agent-staging`).
- `GEMINI_ENTERPRISE_LOCATION`: Discovery Engine location (`global`).
- `GEMINI_ENTERPRISE_ENGINE_ID`: Your Discovery Engine Engine ID.

### Deploy to Vertex AI & Gemini Enterprise
Run the update and patch script to package, deploy to Agent Engine, and link to Discovery Engine:
```bash
python scripts/update_and_patch.py
```
This will:
1. Package the agent dependencies and source files.
2. Deploy the `A2aAgent` to Vertex AI Reasoning Engine.
3. Patch the Gemini Enterprise agent definition with the new endpoint URL and `application/json+a2ui` output modes.

---

## 🧪 Testing in Gemini Enterprise

1. Open your agent in Gemini Enterprise:
   ```
   https://vertexaisearch.cloud.google.com/home/cid/<CUSTOMER_ID>/r/agent/<AGENT_ID>/session/-?hl=en_US
   ```
2. Click **"+ New chat"** in the sidebar.
3. Click the **"+"** attachment button to attach a PDF or Word document (e.g., `5g-edge-computing-value-opportunity.pdf`).
4. Type your prompt:
   > `Translate to German`
5. The agent will:
   - Translate the document preserving formatting and removing watermarks.
   - Localize embedded diagrams and graphics.
   - Run the financial audit.
   - Render the interactive KPMG dashboard and side-by-side visual viewer.
   - Provide a direct clean download link.
6. Refresh the browser page (`F5` / `Cmd+R`) — the dashboard and viewer will reload cleanly without any errors.
