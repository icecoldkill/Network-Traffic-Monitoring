# rag_pipeline.py
"""
RAG (Retrieval-Augmented Generation) Pipeline for Network Security Domain
AI407L Lab Mid Exam - Spring 2026 | Task 1
Student: Ahsan Saleem (2022074)

This module implements a complete RAG pipeline that:
1. Loads domain-specific knowledge documents from knowledge_base/
2. Chunks and embeds them using sentence-transformers
3. Stores embeddings in a FAISS vector store
4. Retrieves relevant context for user queries
5. Generates grounded answers using Groq LLM (Llama3)
"""

import os
import glob
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# LangChain imports — using current (v0.3+) package structure
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

# ── Constants ────────────────────────────────────────────────────────────────
KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")
VECTOR_STORE_DIR = os.path.join(os.path.dirname(__file__), "vector_store")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GROQ_MODEL = "llama-3.3-70b-versatile"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 4


class NetworkSecurityRAG:
    """
    Complete RAG pipeline for the Network Security domain.
    
    Loads markdown documents from the knowledge_base/ directory,
    splits them into chunks, creates FAISS embeddings, and answers
    domain-specific questions using retrieved context + Groq LLM.
    """

    def __init__(
        self,
        knowledge_dir: str = KNOWLEDGE_BASE_DIR,
        embedding_model: str = EMBEDDING_MODEL,
        groq_model: str = GROQ_MODEL,
        groq_api_key: Optional[str] = None,
    ):
        self.knowledge_dir = knowledge_dir
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is required. Set via env or pass groq_api_key."
            )

        # ── 1. Embeddings (local, no API key needed) ─────────────────────
        print(f"[RAG] Loading embedding model: {embedding_model}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        # ── 2. LLM ──────────────────────────────────────────────────────
        self.llm = ChatGroq(
            model=groq_model,
            api_key=self.groq_api_key,
            temperature=0.3,
            max_tokens=2048,
        )

        # ── 3. Vector store (built lazily) ───────────────────────────────
        self.vector_store: Optional[FAISS] = None
        self.rag_chain = None

    # ── Document Loading ─────────────────────────────────────────────────
    def _load_documents(self) -> List[Document]:
        """Load all markdown files from the knowledge_base directory."""
        docs: List[Document] = []
        md_files = glob.glob(os.path.join(self.knowledge_dir, "*.md"))

        if not md_files:
            raise FileNotFoundError(
                f"No .md files found in {self.knowledge_dir}"
            )

        for filepath in md_files:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            doc = Document(
                page_content=content,
                metadata={
                    "source": os.path.basename(filepath),
                    "path": filepath,
                },
            )
            docs.append(doc)
            print(f"[RAG] Loaded: {os.path.basename(filepath)} ({len(content)} chars)")

        return docs

    # ── Chunking ─────────────────────────────────────────────────────────
    def _split_documents(self, docs: List[Document]) -> List[Document]:
        """Split documents into smaller chunks for embedding."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n## ", "\n### ", "\n\n", "\n", " "],
        )
        chunks = splitter.split_documents(docs)
        print(f"[RAG] Split {len(docs)} documents into {len(chunks)} chunks")
        return chunks

    # ── Vector Store ─────────────────────────────────────────────────────
    def build_vector_store(self) -> FAISS:
        """Load documents, chunk them, and build a FAISS vector store."""
        docs = self._load_documents()
        chunks = self._split_documents(docs)

        print("[RAG] Building FAISS vector store …")
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)

        # Persist to disk
        os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
        self.vector_store.save_local(VECTOR_STORE_DIR)
        print(f"[RAG] Vector store saved to {VECTOR_STORE_DIR}")

        return self.vector_store

    def load_vector_store(self) -> FAISS:
        """Load a previously saved FAISS vector store from disk."""
        if not os.path.exists(VECTOR_STORE_DIR):
            print("[RAG] No saved vector store found — building from scratch")
            return self.build_vector_store()
        
        self.vector_store = FAISS.load_local(
            VECTOR_STORE_DIR,
            self.embeddings,
            allow_dangerous_deserialization=True,
        )
        print("[RAG] Loaded vector store from disk")
        return self.vector_store

    # ── Retrieval ────────────────────────────────────────────────────────
    def retrieve(self, query: str, k: int = TOP_K) -> List[Document]:
        """Retrieve the top-k most relevant document chunks for a query."""
        if self.vector_store is None:
            self.build_vector_store()
        results = self.vector_store.similarity_search(query, k=k)
        return results

    # ── RAG Chain (LCEL — modern LangChain) ──────────────────────────────
    def _build_rag_chain(self):
        """Build the RAG chain using LangChain Expression Language (LCEL)."""
        if self.vector_store is None:
            self.build_vector_store()

        retriever = self.vector_store.as_retriever(search_kwargs={"k": TOP_K})

        prompt = ChatPromptTemplate.from_template(
            """You are a Network Security Expert Assistant. Use the following 
retrieved context to answer the user's question accurately. If the context does 
not contain enough information, say so and provide your best general knowledge.

RETRIEVED CONTEXT:
{context}

USER QUESTION: {question}

Provide a detailed, professional answer grounded in the retrieved context:"""
        )

        def format_docs(docs: List[Document]) -> str:
            return "\n\n---\n\n".join(
                f"[Source: {d.metadata.get('source', 'unknown')}]\n{d.page_content}"
                for d in docs
            )

        self.rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        # Also store retriever for source document access
        self._retriever = retriever
        return self.rag_chain

    # ── Public Query Interface ───────────────────────────────────────────
    def query(self, question: str) -> Dict[str, Any]:
        """
        Answer a question using the full RAG pipeline:
        embed query → retrieve context → generate answer.
        
        Returns dict with 'answer', 'source_documents', and 'retrieved_context'.
        """
        if self.rag_chain is None:
            self._build_rag_chain()

        print(f"\n[RAG] Query: {question}")
        print("[RAG] Retrieving relevant context …")

        # Retrieve documents for transparency
        retrieved_docs = self.retrieve(question)
        retrieved_context = "\n---\n".join(
            [
                f"[Source: {d.metadata.get('source', 'unknown')}]\n{d.page_content}"
                for d in retrieved_docs
            ]
        )

        # Run the RAG chain
        answer = self.rag_chain.invoke(question)

        print(f"[RAG] Retrieved {len(retrieved_docs)} source chunks")
        print(f"[RAG] Answer generated ({len(answer)} chars)")

        return {
            "answer": answer,
            "source_documents": [
                {
                    "content": doc.page_content[:200] + "…",
                    "source": doc.metadata.get("source", "unknown"),
                }
                for doc in retrieved_docs
            ],
            "retrieved_context": retrieved_context,
        }


# ── Standalone Demo ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("  Network Security RAG Pipeline — Demo")
    print("  AI407L Mid-Exam | Ahsan Saleem (2022074)")
    print("=" * 70)

    rag = NetworkSecurityRAG()
    rag.build_vector_store()

    # ── Demo queries ─────────────────────────────────────────────────────
    demo_questions = [
        "What are the different types of DDoS attacks and how can they be detected in network traffic?",
        "Describe the CIC-IDS2018 dataset and what attack types it contains.",
        "What are the best practices for blocking a suspicious IP address?",
    ]

    for q in demo_questions:
        print("\n" + "─" * 70)
        result = rag.query(q)
        print(f"\n📝 ANSWER:\n{result['answer']}")
        print(f"\n📚 Sources used: {[s['source'] for s in result['source_documents']]}")
        print("─" * 70)
