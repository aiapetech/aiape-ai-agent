
import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import engine as postgres_engine
from models.postgres_models import *
from sqlmodel import Field, Session, select
from core.components import embedding, text_splitter
import dotenv
from datetime import datetime
from sqlalchemy import func
from langchain_core.prompts import PromptTemplate
import json
from core.query_templates import prompt as prompt_template
from langchain_openai import ChatOpenAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.schema.document import Document
from stqdm import stqdm
from core.config import settings as app_settings
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_community.document_loaders import WebBaseLoader



dotenv.load_dotenv()
CWD = os.getcwd()
class ChainSetting:
    MODEL_PROVIDER = "openai"
    CHUNCK_SIZE = 1000
    CHUNK_OVERLAP = 200
    QDRANT_COLLECTION_NAME = app_settings.QDRANT_COLLECTION_NAME
    with open(f"{CWD}/data/list_of_project.json") as f:
        LIST_OF_PROJECT_INFO = json.load(f)
    OPENAI_MODEL_NAME = app_settings.OPENAI_MODEL_NAME
    OPENAI_EMBEDDING_MODEL_NAME = app_settings.OPENAI_EMBEDDING_MODEL_NAME

class PostProcessor:
    def __init__(self, settings: ChainSetting, postgres_engine):
        self.text_embedder_component = embedding.TextEmbeddingComponent(model_provider=settings.MODEL_PROVIDER)
        #self.vector_store_component = vector_store.QdrantVectorStoreComponent(embedding_model=self.text_embedder_component.embedding_model,collection_name=settings.QDRANT_COLLECTION_NAME)
        self.text_splitter_component = text_splitter.TextSplitterComponent(chunk_size=settings.CHUNCK_SIZE,chunk_overlap=settings.CHUNK_OVERLAP)
        self.postgres_engine = postgres_engine
        if settings.MODEL_PROVIDER == "openai":
            self.llm = ChatOpenAI(model=settings.OPENAI_MODEL_NAME)
        elif settings.MODEL_PROVIDER == "google":
            self.llm = ChatGoogleGenerativeAI("gemini-1.5-flash")
        self.settings = settings
        
    def get_data_by_date(self,date: str, post_id: int = None):
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        with Session(self.postgres_engine) as session:
            if post_id:
                statement = select(Posts).where(func.date(Posts.posted_at) == date_obj.date(),Posts.id == post_id)
            else:
                statement = select(Posts).where(func.date(Posts.posted_at) == date_obj.date())
            results = session.exec(statement).fetchall()
        return results

    def store_vectors(self, contents: list, metadata: list):
        if len(contents):
            #result = self.vector_store_component.bulk_upsert_vectors(contents,metadata)
            post_id = metadata[0]["post_id"]
            #Update the status in the database
            with Session(self.postgres_engine) as session:
                statement = select(Posts).where(Posts.id == post_id)
                results = session.exec(statement)
                post = results.one()
                post.status = "processed"
                
                session.add(post)
                session.commit()
                session.refresh(post)
                return results
        else:
            print("No content to store")
            return None
    
    def embed_text(self, text: str):
        return self.text_embedder_component.embed_text(text)
    
    def determine_post_subject(self, texts: str):
        if isinstance(texts, str):
            docs = [Document(page_content=docs)]
        elif isinstance(texts,list):
            docs = [Document(page_content=doc) for doc in texts]
        prompt = PromptTemplate(
            template = prompt_template.CRYPTO_MENTION_EXTRACTION_PROMPT,
            input_variables=["context"],
            partial_variables={"list_of_project_names": self.settings.LIST_OF_PROJECT_INFO}
            )
        chain = create_stuff_documents_chain(self.llm, prompt)
        res = chain.invoke({"context": docs})
        if isinstance(res,dict):
            return res['output_text']
        else:
            return res

    def sentiment_analysis(self, texts: str):
        if isinstance(texts, str):
            docs = [Document(page_content=docs)]
        elif isinstance(texts,list):
            docs = [Document(page_content=doc) for doc in texts]
        prompt = PromptTemplate(
            template = prompt_template.CRYPTO_SENTIMENT_PROMPT,
            input_variables=["context"]
            )
        chain = create_stuff_documents_chain(self.llm, prompt)
        res = chain.invoke({"context": docs})
        if isinstance(res,dict):
            return res['output_text']
        else:
            return res
    
    def subject_detection(self, texts):
        if isinstance(texts, str):
            docs = [Document(page_content=docs)]
        elif isinstance(texts,list):
            docs = [Document(page_content=doc) for doc in texts]
        prompt = PromptTemplate(
            template = prompt_template.CRYPTO_SENTIMENT_PROMPT,
            input_variables=["text"],
            partial_variables={"list_of_project_names": self.settings.LIST_OF_PROJECT_INFO}
            )
        chain = create_stuff_documents_chain(self.llm, prompt)
        res = chain.invoke({"text": docs})
        if isinstance(res,dict):
            return res['output_text']
        else:
            return res
    
    def project_name_extraction(self, texts):
        if isinstance(texts, str):
            docs = [Document(page_content=texts)]
        elif isinstance(texts,list):
            docs = [Document(page_content=doc) for doc in texts]
        prompt = PromptTemplate(
            template = prompt_template.CRYPTO_PROJECT_EXTRACTION_PROMPT,
            input_variables=["context"],
            partial_variables={"list_of_project_names": self.settings.LIST_OF_PROJECT_INFO}
            )
        chain = create_stuff_documents_chain(self.llm, prompt)
        res = chain.invoke({"context": docs})
        if isinstance(res,dict):
            return res['output_text']
        else:
            return res
    
    def summarize_text(self, texts):
        if isinstance(texts, str):
            docs = [Document(page_content=docs)]
        elif isinstance(texts,list):
            docs = [Document(page_content=doc) for doc in texts]
        prompt = PromptTemplate(
            template = prompt_template.TEXT_SUMMARIZATION_PROMPT,
            partial_variables={"list_of_project_names": self.settings.LIST_OF_PROJECT_INFO}
            )
        #llm_chain = LLMChain(llm=self.llm, prompt=prompt)
        stuff_chain = create_stuff_documents_chain(llm=self.llm, document_variable_name="text",prompt=prompt)
        res = stuff_chain.invoke({"text":docs})
        if isinstance(res,dict):
            return res['output_text']
        else:
            return res
    
    def keyword_extraction(self, texts):
        if isinstance(texts, str):
            docs = [Document(page_content=docs)]
        elif isinstance(texts,list):
            docs = [Document(page_content=doc) for doc in texts]
        prompt = PromptTemplate(
            template = prompt_template.KEYWORD_EXTRACTION_PROMPT,
            input_variables=["context"],
            partial_variables={"list_of_project_names": self.settings.LIST_OF_PROJECT_INFO}
            )
        chain = create_stuff_documents_chain(self.llm, prompt)
        res = chain.invoke({"context": docs})
        if isinstance(res,dict):
            return res['output_text']
        else:
            return res
    
    def project_category_extraction(self, texts):
        if isinstance(texts, str):
            docs = [Document(page_content=docs)]
        elif isinstance(texts,list):
            docs = [Document(page_content=doc) for doc in texts]
        prompt = PromptTemplate(
            template = prompt_template.CRYPTO_PROJECT_CATEGORY_EXTRACTION_PROMPT,
            input_variables=["context"],
            partial_variables={"list_of_project_names": self.settings.LIST_OF_PROJECT_CATEGORY_INFO}
            )
        chain = create_stuff_documents_chain(self.llm, prompt)
        res = chain.invoke({"context": docs})
        if isinstance(res,dict):
            return res['output_text']
        else:
            return res

    def analyze_posts(self, date: str, post_id: int=None):
        raw_data = self.get_data_by_date(date,post_id=post_id)
        session = Session(self.postgres_engine)
        sentiment = None
        project_name = None
        summarization = None
        is_mentioned = False
        keywords = None
        for data in stqdm(raw_data):
            #1. Determine the subject of the post
            docs = self.text_splitter_component.split_text(data.content)
            is_crypto_subject = self.determine_post_subject(docs)
            if "true" in is_crypto_subject.lower():
                is_mentioned = True
            if is_mentioned:
                #2. Sentiment analysis
                sentiment = self.sentiment_analysis(docs)
                
                #3. Project name extraction
                project_name = self.project_name_extraction(docs)
                #project_category = project_name.split(",")
                # keywords = self.keyword_extraction(docs)
                # keywords = keywords.split(",")
            #4. Summarization
            summarization = self.summarize_text(docs)
            #5. Store the processed resultss
            statement = select(ProcessedResults).where(ProcessedResults.post_id == data.id)
            results = session.exec(statement)
            procressed_result = results.first()
            if procressed_result is None:
                procressed_result = ProcessedResults(
                is_mentioned=is_mentioned,
                sentiment=sentiment,
                project_name=project_name,
                summarization=summarization,
                keywords=keywords,
                post_id=data.id,
                processed_at=datetime.now()
            )
            else:
                procressed_result.is_mentioned = is_mentioned
                procressed_result.sentiment = sentiment
                procressed_result.project_name = project_name
                procressed_result.summarization = summarization
                procressed_result.keywords = keywords
                procressed_result.processed_at = datetime.now()
            post = session.get(Posts,data.id)
            post.status = "processed"
            session.add(post)
            session.add(procressed_result)
            session.commit()
        session.close()
        return True
    
    def generate_content(self, token_data):
        url = token_data['links']['homepage'][0]
        market_data = token_data['market_data']
        today_market_data = {
            "current_price":market_data['current_price']['usd'],
            "market_cap":market_data['market_cap']['usd'],
            "market_cap_rank":market_data['market_cap_rank'],
            "total_volume":market_data['total_volume']['usd'],
            "price_change_percentage_24h":market_data['price_change_percentage_24h'],
            "price_change_24h":market_data['price_change_24h']
        }
        description = token_data['description']['en']
        project_name = token_data['name']
        ## Process url
        loader = WebBaseLoader(url)
        docs = loader.load()
        prompt = PromptTemplate(
            template = prompt_template.PROJECT_SUMMARIZATION_PROMPT,
            input_variables=["context"],
            partial_variables={
                "project_name":project_name,
                "project_description":description,
                "today_market_data":today_market_data,

                }
            )
        chain = create_stuff_documents_chain(self.llm, prompt)
        res = chain.invoke({"context": docs})
        if isinstance(res,dict):
            return res['output_text']
        else:
            return res


from langchain.vectorstores.docarray import DocArrayInMemorySearch
from langchain_openai import OpenAIEmbeddings
from langchain.chains.retrieval_qa.base import RetrievalQA



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
    

        
        

if __name__ == "__main__":
    settings = ChainSetting()
    post_processor = PostProcessor(settings, postgres_engine)
    with open(f"{CWD}/token_market_data.json") as f:
        token_data = json.load(f)
    reports = []
    for token in token_data:
        report = post_processor.generate_content(token)
        reports.append(report)
    #post_processor.analyze_posts(date = "2025-01-29")
    pass