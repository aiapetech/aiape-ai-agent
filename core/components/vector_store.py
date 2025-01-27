from langchain_qdrant import QdrantVectorStore
from qdrant_client.http.models import Distance, VectorParams
from langchain_core.documents import Document
from core.qdrant import init_qdrant_client
from uuid import uuid4


class QdrantVectorStoreComponent():
    def __init__(self,embedding_model,collection_name):
        self.client = init_qdrant_client()
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.vector_store = QdrantVectorStore(
                    client=self.client,
                    collection_name=self.collection_name,
                    embedding=self.embedding_model,
                )
    
    def create_collection(self,collection_name,vectors_config):
        self.client.create_collection(collection_name=collection_name,vectors_config=vectors_config)
    
    def delete_vector(self,ids):
        self.vector_store.delete(ids)

    def bulk_upsert_vectors(self,contents,metadata):
        documents = []
        
        for content,meta in zip(contents,metadata):
            document = Document(
                page_content=content,
                metadata=meta,
            )
            documents.append(document)
        uuids = [str(uuid4()) for _ in range(len(documents))]
        res = self.vector_store.add_documents(documents,ids=uuids)
        return res
    
    
    def upsert_vector(self,content,id,metadata):
        document = Document(
            page_content=content,
            metadata=metadata,
        )
        res = self.vector_store.add_documents([document],ids=[id])
        return res
