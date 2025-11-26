from langfuse import Langfuse
from langfuse.client import DatasetClient

def get_golden_dataset(langfuse_client: Langfuse, dataset_name: str) -> DatasetClient:
    return langfuse_client.get_dataset(name=dataset_name, fetch_items_page_size=100)
