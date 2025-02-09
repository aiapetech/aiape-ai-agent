import os,sys
sys.path.append(os.getcwd())
from langchain_qdrant import QdrantVectorStore
from qdrant_client.http.models import Distance, VectorParams
from langchain_core.documents import Document
from core.qdrant import init_qdrant_client
from uuid import uuid4
from core.db import engine as postgres_engine   
import pandas as pd 
from core.config import settings


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
    
    def search_vector(self,content,metadata):
        document = Document(
            page_content=content,
            metadata=metadata,
        )
        res = self.vector_store.search(document)
        return res
    def query_qdrant(self,query,top_k=20):

    # Creates embedding vector from user query
        embedded_query = self.client.embed(
            text=query,
            model_name=self.embedding_model
        )
        query_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=(
                'content', embedded_query
            ),
            limit=top_k, 
            query_filter=None
        )
        
        return query_results

def insert_data():
    posts = pd.read_sql("SELECT p.id post_id, p.posted_at, p.content, a.name author_name, p.link, p.status FROM posts p left join profiles a on p.author_id = a.id", postgres_engine)
    contents = posts.content.tolist()
    metadata = posts.to_dict(orient="records")
    embedding_model = settings.OPENAI_EMBEDDING_MODEL_NAME
    qdrant_vector_store = QdrantVectorStoreComponent(embedding_model,"posts")
    qdrant_vector_store.bulk_upsert_vectors(contents,metadata)


if __name__=="__main__":
    insert_data()