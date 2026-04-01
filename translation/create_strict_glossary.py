import os

# Financial terms that should NOT be translated (Stopwords)
stopwords_glossary_content = """en,de,ja
"EBITDA","EBITDA","EBITDA"
"GAAP","GAAP","GAAP"
"GDPR","GDPR","GDPR"
"BlackRock","BlackRock","BlackRock"
"Goldman Sachs","Goldman Sachs","Goldman Sachs"
"ROI","ROI","ROI"
"KPIs","KPIs","KPIs"
"""

os.makedirs('UP_Demos/translation/glossaries', exist_ok=True)
with open('UP_Demos/translation/glossaries/glossary_stopwords.csv', 'w', encoding='utf-8') as f:
    f.write(stopwords_glossary_content)

print("Created strict stopwords glossary: UP_Demos/translation/glossaries/glossary_stopwords.csv")
