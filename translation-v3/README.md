# Financial Document Translation Agent

Expert document translation with **numerical precision**, **layout preservation**, and **terminology consistency**.

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r UP_Demos/translation/requirements.txt
   ```

2. **Generate Test Assets**:
   These scripts create the sample financial report and the multilingual glossaries (German/Japanese).
   ```bash
   python3 UP_Demos/translation/generate_test_data.py
   python3 UP_Demos/translation/create_glossary.py
   ```

3. **Run the Agent**:
   Launch the agent via the ADK CLI to start the translation orchestration.
   ```bash
   adk run UP_Demos/translation/main.py
   ```

## Key Files
- `main.py`: The `FinanceTranslator` agent definition.
- `translator_tool.py`: Core logic for Cloud Translation API integration.
- `sample_doc.pdf`: The dummy financial report with YoY metrics.
- `financial_glossary_de.csv`: German financial terminology.
- `financial_glossary_ja.csv`: Japanese financial terminology.

## Deployment Checklist
- [ ] Enable **Cloud Translation API** in your GCP console.
- [ ] Upload the glossary CSVs to a GCS bucket.
- [ ] Register the glossaries using the `gcloud` commands printed by `create_glossary.py`.
- [ ] Update `GOOGLE_CLOUD_PROJECT` in your `.env` file.
