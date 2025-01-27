
from qdrant_client import QdrantClient
from core.config import settings



def init_qdrant_client():   
    client = QdrantClient(url=settings.QDRANT_SERVER)
    return client

# def upsert(qdrant_client, collection_name, data):
#     res = qdrant_client.upsert(collection_name, data)
#     return res

# def search(qdrant_client, collection_name, query):
#     res = qdrant_client.search(collection_name, query)
#     return res

# def delete(qdrant_client, collection_name, ids):
#     res = qdrant_client.delete(collection_name, ids)
#     return res
