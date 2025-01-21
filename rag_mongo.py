import os
import sys
import json
from dotenv import load_dotenv
from langchain.docstore.document import Document
from typing import List, Any
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.retrievers import BaseRetriever
from sentence_transformers import CrossEncoder
from pydantic import BaseModel, Field
import argparse
from langchain import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pymongo import MongoClient

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
from tests import *
from evaluate.evaluate_rag import *

# Загрузка переменных окружения
load_dotenv()

# Установите переменные окружения для подключения к MongoDB
MONGO_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = os.getenv("MONGO_INITDB_ROOT_PORT")

mongo_uri = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
client = MongoClient(mongo_uri)
db = client["llm_database"]
collection = db["exp_fm_jun_3"]

# Установите OpenAI API ключ
os.environ["OPENAI_API_KEY"] = 'sk-6B8eZ_la_-IyLLSTuH6iiDUwsR4Ccc0QmMsdRJfE1KT3BlbkFJ5bxuCmk5FsxQ_VTRKfsxRhpx3Ji6WwJlk6hldwXWEA'

# Helper Classes and Functions

class RatingScore(BaseModel):
    relevance_score: float = Field(..., description="The relevance score of a document to a query.")

def rerank_documents(query: str, docs: List[Document], top_n: int = 3) -> List[Document]:
    prompt_template = PromptTemplate(
        input_variables=["query", "doc"],
        template="""On a scale of 1-10, rate the relevance of the following document to the query. Consider the specific context and intent of the query, not just keyword matches.
        Query: {query}
        Document: {doc}
        Relevance Score:"""
    )

    llm = ChatOpenAI(temperature=0, model_name="gpt-4o", max_tokens=4000)
    llm_chain = prompt_template | llm.with_structured_output(RatingScore)

    scored_docs = []
    for doc in docs:
        input_data = {"query": query, "doc": doc.page_content}
        score = llm_chain.invoke(input_data).relevance_score
        try:
            score = float(score)
        except ValueError:
            score = 0  # Default score if parsing fails
        scored_docs.append((doc, score))

    reranked_docs = sorted(scored_docs, key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in reranked_docs[:top_n]]

class CustomRetriever(BaseRetriever, BaseModel):
    vectorstore: Any = Field(description="Vector store for initial retrieval")

    class Config:
        arbitrary_types_allowed = True

    def get_relevant_documents(self, query: str, num_docs=2) -> List[Document]:
        initial_docs = self.vectorstore.similarity_search(query, k=30)
        return rerank_documents(query, initial_docs, top_n=num_docs)

class CrossEncoderRetriever(BaseRetriever, BaseModel):
    vectorstore: Any = Field(description="Vector store for initial retrieval")
    cross_encoder: Any = Field(description="Cross-encoder model for reranking")
    k: int = Field(default=5, description="Number of documents to retrieve initially")
    rerank_top_k: int = Field(default=3, description="Number of documents to return after reranking")

    class Config:
        arbitrary_types_allowed = True

    def get_relevant_documents(self, query: str) -> List[Document]:
        initial_docs = self.vectorstore.similarity_search(query, k=self.k)
        pairs = [[query, doc.page_content] for doc in initial_docs]
        scores = self.cross_encoder.predict(pairs)
        scored_docs = sorted(zip(initial_docs, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored_docs[:self.rerank_top_k]]

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        raise NotImplementedError("Async retrieval not implemented")

def compare_rag_techniques(query: str, docs: List[Document]) -> None:
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)

    print("Comparison of Retrieval Techniques")
    print("==================================")
    print(f"Query: {query}\n")

    print("Baseline Retrieval Result:")
    baseline_docs = vectorstore.similarity_search(query, k=2)
    for i, doc in enumerate(baseline_docs):
        print(f"\nDocument {i + 1}:")
        print(doc.page_content)

    print("\nAdvanced Retrieval Result:")
    custom_retriever = CustomRetriever(vectorstore=vectorstore)
    advanced_docs = custom_retriever.get_relevant_documents(query)
    for i, doc in enumerate(advanced_docs):
        print(f"\nDocument {i + 1}:")
        print(doc.page_content)

# Main class
class RAGPipeline:
    def __init__(self, path: str):
        self.vectorstore = self.encode_json(path)
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-4o")

    def encode_json(self, path: str):
        """Load JSON data and convert it into Document objects for the vector store."""
        with open(path, 'r') as f:
            gpus = json.load(f)

        # Convert JSON data into Document objects
        docs = []
        for gpu in gpus:
            # Handle None values
            average_price = gpu.get('average_price', 0)  # Default to 0 if None
            doc_content = f"""
            Chipset: {gpu['chipset']}
            Memory: {gpu['memory']} GB
            Core Clock: {gpu['core_clock']} MHz
            Boost Clock: {gpu['boost_clock']} MHz
            Length: {gpu['length']} mm
            Rating: {gpu['rating']}
            Architecture: {gpu['architecture']}
            Release Year: {gpu['release_year']}
            Power Consumption: {gpu['power_consumption']}
            Average Price: ₹{average_price:.2f}
            """
            docs.append(Document(page_content=doc_content))

        # Create a vector store from the documents
        embeddings = OpenAIEmbeddings()
        return FAISS.from_documents(docs, embeddings)

    def run(self, query: str, retriever_type: str = "reranker"):
        if retriever_type == "reranker":
            retriever = CustomRetriever(vectorstore=self.vectorstore)
        elif retriever_type == "cross_encoder":
            cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            retriever = CrossEncoderRetriever(
                vectorstore=self.vectorstore,
                cross_encoder=cross_encoder,
                k=10,
                rerank_top_k=5
            )
        else:
            raise ValueError("Unknown retriever type. Use 'reranker' or 'cross_encoder'.")

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )

        result = qa_chain({"query": query})

        print(f"\nQuestion: {query}")
        print(f"Answer: {result['result']}")
        print("\nRelevant source documents:")
        for i, doc in enumerate(result["source_documents"]):
            print(f"\nDocument {i + 1}:")
            print(doc.page_content[:200] + "...")

# Argument Parsing
def parse_args():
    parser = argparse.ArgumentParser(description="RAG Pipeline")
    parser.add_argument("--path", type=str, default="data/video_card_merged.json", help="Path to the JSON file")
    parser.add_argument("--query", type=str, default='What is the best GPU for gaming?', help="Query to ask")
    parser.add_argument("--retriever_type", type=str, default="reranker", choices=["reranker", "cross_encoder"],
                        help="Type of retriever to use")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    pipeline = RAGPipeline(path=args.path)
    pipeline.run(query=args.query, retriever_type=args.retriever_type)

    # Demonstrate the reranking comparison with GPU-related examples
    chunks = [
        "The GeForce RTX 4090 is the most powerful GPU, with 24GB of memory and a rating of 100.",
        "The Radeon RX 6900 XT is a great GPU for gaming, with 16GB of memory and a rating of 95.",
        "The GeForce RTX 3080 is a mid-range GPU, with 10GB of memory and a rating of 85.",
        "The GeForce RTX 4070 Ti is a high-performance GPU, with 12GB of memory and a rating of 90.",
        "The Radeon RX 6700 XT is a budget-friendly GPU, with 12GB of memory and a rating of 80."
    ]
    docs = [Document(page_content=sentence) for sentence in chunks]

    # Compare retrieval techniques for a query
    compare_rag_techniques(query="Which GPU should I buy for gaming?", docs=docs)
