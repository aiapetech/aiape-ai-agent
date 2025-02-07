


from langchain_openai import OpenAIEmbeddings
import os
from langchain.document_loaders import CSVLoader

from langchain_openai import OpenAI

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.vectorstores.docarray import DocArrayInMemorySearch
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_openai import ChatOpenAI
from langchain.indexes import VectorstoreIndexCreator
from langchain_community.document_loaders import WebBaseLoader



url = "https://raw.githubusercontent.com/UKPLab/sentence-transformers/master/examples/datasets/faq-ukp.csv"
loader = WebBaseLoader(url)
docs = loader.load()
openai_api_key = os.environ.get("OPENAI_API_KEY")
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
index = VectorstoreIndexCreator(vectorstore_cls=DocArrayInMemorySearch, embedding=embeddings).from_loaders([loader])


from langchain.indexes import VectorstoreIndexCreator

from langchain_openai import ChatOpenAI

db = DocArrayInMemorySearch.from_documents(docs, embedding=embeddings)
query = "Please suggest a shirt with sunblocking"
docs = db.similarity_search(query)
retriever = db.as_retriever()
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo")

qa_stuff = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, verbose=True)

response = qa_stuff.invoke(query)


index = VectorstoreIndexCreator(

    vectorstore_cls=DocArrayInMemorySearch,

    embedding=embeddings,

).from_loaders([loader])
response = index.query(query, llm=llm)
