from langchain_openai import OpenAIEmbeddings
from langchain_google_vertexai import VertexAIEmbeddings
from core.config import settings


class TextEmbeddingComponent:
    def __init__(self, model_provider: str, model_name: str=None):
        if model_provider == "openai":
            if not model_name:
                self.model_name = settings.DEFAULT_OPENAI_EMBEDDING_MODEL
            self.embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
        
        elif model_provider == "google":
            if not model_name:
                self.model_name = settings.DEFAULT_GOOGLE_EMBEDDING_MODEL
            self.embedding_model = VertexAIEmbeddings(model="text-embedding-004")
        else:
            raise ValueError("Invalid model provider")

    def embed_text(self, text: str):
        return self.embedding_model.embed_query(text)
