from langchain.vectorstores.docarray import DocArrayInMemorySearch
from langchain_openai import OpenAIEmbeddings
from langchain.chains.retrieval_qa.base import RetrievalQA

import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.postgres_models import *
import dotenv
from datetime import datetime
from sqlalchemy import func
from langchain_core.prompts import PromptTemplate
from core.query_templates import prompt as prompt_template
from langchain_openai import ChatOpenAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from core.config import settings as app_settings
#from core.components.vector_store import QdrantVectorStore
from langchain_community.document_loaders import WebBaseLoader



class QARetriver:
    def __init__(self,url,token_data,settings):
        self.llm = ChatOpenAI(model=settings.OPENAI_MODEL_NAME)
        self.embeddings = OpenAIEmbeddings(model=settings.OPENAI_EMBEDDING_MODEL_NAME)
        loader= WebBaseLoader(url)
        self.docs = loader.load()
        self.db = DocArrayInMemorySearch.from_documents(self.docs, embedding=self.embeddings)
        self.token_data = token_data
        project_name = token_data['name']
        description = token_data['description']['en']
        market_data = token_data['market_data']
        self.prompt = PromptTemplate(
            template = prompt_template.TOKEN_ASSITANT,
            input_variables=["context","question"],
            partial_variables={
                "project_name":project_name,
                "project_description":description,
                "today_market_data":market_data,

                }
            )
        #self.prompt=PromptTemplate(template=prompt_template,input_variables=["context","question"])

    def retrieve(self,query):
        retriever = self.db.as_retriever()
        retrievalQA=RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt":self.prompt}
        )

        result = retrievalQA.invoke({"query": query})
        return result['result']
    
