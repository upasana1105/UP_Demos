from google.cloud import bigquery

client = bigquery.Client(project="uppdemos")

print("Listing all datasets in project 'uppdemos'...")
try:
    datasets = list(client.list_datasets())
    if not datasets:
        print("No datasets found.")
    for dataset in datasets:
        print(f"\nDataset: {dataset.dataset_id}")
        tables = list(client.list_tables(dataset.dataset_id))
        for table in tables:
            print(f"  - Table/View: {table.table_id}")
except Exception as e:
    print(f"Error: {e}")
