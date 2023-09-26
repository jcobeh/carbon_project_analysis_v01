import os
from dotenv import load_dotenv
import logging
from langchain.docstore.document import Document

from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.document_loaders import TextLoader
from langchain.document_loaders import DirectoryLoader
from langchain.embeddings import GPT4AllEmbeddings
from langchain.embeddings import HuggingFaceEmbeddings

from src.project import Project

load_dotenv()
openai_api_key: str = os.environ.get("OPENAI_API_KEY")


def project_documents_llm_processor(project: Project, query):
    logger = logging.getLogger('MyApp')
    logger.info('Starting the llm function')
    project_proponent_documents = [doc for doc in project.documents if doc.doc_type in [11, 12, 13]]

    # create langchain documents from the variable above
    logger.info('Parsing the docs into langchain documents')
    project_proponent_lc_documents = [Document(page_content=doc.text) for doc in project_proponent_documents]
    logger.info('Splitting the documents into chunks')
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=40)
    texts = text_splitter.split_documents(project_proponent_lc_documents)

    '''
    Embedding Code Piece:
    '''
    # embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)
    embedding = GPT4AllEmbeddings()
    # model_name = "sentence-transformers/all-mpnet-base-v2"
    # model_kwargs = {'device': 'cpu'}
    # encode_kwargs = {'normalize_embeddings': False}
    # embedding = HuggingFaceEmbeddings(
    #     model_name=model_name,
    #     model_kwargs=model_kwargs,
    #     encode_kwargs=encode_kwargs
    # )

    logger.info('Creating the vector database and storing the embeddings')
    vectordb = FAISS.from_documents(documents=texts, embedding=embedding)
    retriever = vectordb.as_retriever()
    # retriever = vectordb.as_retriever(search_kwargs={"k": 5}) -> maybe this is better?
    # docs = retriever.get_relevant_documents(query) -> rather fyi

    logger.info('Creating the llm chain')
    qa_chain = RetrievalQA.from_chain_type(llm=OpenAI(),
                                           chain_type="stuff",
                                           retriever=retriever,
                                           return_source_documents=True)
    logger.info('Querying the llm chain')
    llm_response = qa_chain(query)
    process_llm_response(llm_response)


def process_llm_response(llm_response):
    print(llm_response['result'])
    print('\n\nSources:')
    for source in llm_response["source_documents"]:
        print(source)
