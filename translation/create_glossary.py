import csv
import os

def create_financial_glossary(filename, target_lang):
    # Terms for financial glossary
    # Format: source, target
    glossaries = {
        'de': [
            ('EBITDA', 'EBITDA'), # Protected
            ('Fiscal Year', 'Geschäftsjahr'),
            ('Operating Margin', 'Operative Marge'),
            ('Net Income', 'Nettoergebnis'),
            ('Balance Sheet', 'Bilanz'),
            ('Shareholder Equity', 'Eigenkapital')
        ],
        'ja': [
            ('EBITDA', 'EBITDA'), # Protected
            ('Fiscal Year', '会計年度'),
            ('Operating Margin', '営業利益率'),
            ('Net Income', '純利益'),
            ('Balance Sheet', '貸借対照表'),
            ('Shareholder Equity', '株主資本')
        ]
    }

    
    terms = glossaries.get(target_lang, [])
    
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for term in terms:
            writer.writerow(term)
    
    print(f"Generated {target_lang} financial glossary CSV: {filename}")

def print_upload_instructions(lang_code):
    print(f"\n--- Glossary Upload Instructions ({lang_code}) ---")
    print(f"1. Upload the CSV to a GCS bucket: gsutil cp financial_glossary_{lang_code}.csv gs://YOUR_BUCKET/")
    print(f"2. Call the CreateGlossary API method providing the GCS path.")
    print("Example gcloud command (V3 API):")
    print(f"  gcloud alpha ml translate glossaries create financial_glossary_{lang_code} \\")
    print(f"    --source-lang=en --target-lang={lang_code} \\")
    print(f"    --input-file=gs://YOUR_BUCKET/financial_glossary_{lang_code}.csv")

if __name__ == "__main__":
    create_financial_glossary('UP_Demos/translation/financial_glossary_de.csv', 'de')
    create_financial_glossary('UP_Demos/translation/financial_glossary_ja.csv', 'ja')
    print_upload_instructions('de')
    print_upload_instructions('ja')
