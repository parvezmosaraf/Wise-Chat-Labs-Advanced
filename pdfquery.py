import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.document_loaders import PyPDFium2Loader
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI


class PDFQuery:
    def __init__(self, openai_api_key=None) -> None:
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        os.environ["OPENAI_API_KEY"] = openai_api_key
        # Adjust chunk_size and chunk_overlap for better handling of large documents
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.5, openai_api_key=openai_api_key)
        self.chain = None
        self.db = None
    
    
    def ask(self, question: str) -> str:
        if self.chain is None:
            response = "Please, add a document."
        else:
            docs = self.db.get_relevant_documents(question)
        # to better suit GPT-4's input format for optimal results.
            response = self.chain.run(input_documents=docs, question=question)
        return response



    def ingest(self, file_path: os.PathLike) -> None:
            loader = PyPDFium2Loader(file_path)
            documents = loader.load()
            splitted_documents = self.text_splitter.split_documents(documents)
            self.db = Chroma.from_documents(splitted_documents, self.embeddings).as_retriever()
            self.chain = load_qa_chain(self.llm, chain_type="stuff")

    def forget(self) -> None:
        self.db = None
        self.chain = None