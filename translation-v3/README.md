# Financial Document Translation Agent (v3)

Expert document translation with **numerical precision**, **layout preservation**, and **terminology consistency**. Now supports PDF, DOCX, and PPTX formats with AI-powered image localization.

## New Features in v3
- **Multi-Format Support**: Seamlessly handles `.pdf`, `.docx`, and `.pptx` documents.
- **AI Image Localization**: Uses `gemini-2.5-flash-image` to translate text embedded within images, charts, and diagrams while preserving layout.
- **Fallback Pipeline**: Automatically falls back to full Gemini translation for scanned or non-selectable vector documents.

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js (for frontend)
- GCP Project with **Cloud Translation API** enabled.

### Installation

1. **Clone the workspace** and navigate to the project directory:
   ```bash
   cd "UP_Demos/translation-v3"
   ```

2. **Install Backend Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Frontend Dependencies**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### Running the Application

Use the provided runner script to start both the backend and frontend:
```bash
bash run.sh
```

- **Frontend Dashboard**: `http://localhost:5175`
- **Backend API**: `http://localhost:8002`

## Key Files
- `main.py`: The `FinanceTranslator` agent definition.
- `translator_tool.py`: Core logic for Cloud Translation API and Gemini image localization.
- `audit_tool.py`: Text extraction utilities for PDF, DOCX, and PPTX.
- `server.py`: FastAPI backend orchestrator.
- `frontend/`: React/Vite dashboard for uploading and viewing translations.

## Deployment Checklist
- [ ] Enable **Cloud Translation API** in your GCP console.
- [ ] Upload the glossary CSVs to a GCS bucket if using Cloud Glossaries.
- [ ] Update `GOOGLE_CLOUD_PROJECT` in your environment or `.env` file.
