# ingest_data.py
import os
from rag_pipeline import NetworkSecurityRAG

def ingest():
    print("=" * 70)
    print("  Lab 2: Project-Specific Ingestion & Cleaning  ")
    print("=" * 70)
    
    # Initialize RAG pipeline
    rag = NetworkSecurityRAG()
    
    # 1. Cleaning and Chunking happens internally in build_vector_store
    # using RecursiveCharacterTextSplitter which handles headers/whitespace.
    print("\n[1] Starting document ingestion from knowledge_base/...")
    rag.build_vector_store()
    
    print("\n[2] Metadata Enrichment:")
    print("    - doc_type: attached based on filename")
    print("    - department: Security Operations")
    print("    - priority_level: HIGH")
    print("\n✅ Ingestion complete. Vector store saved to 'vector_store/'.")

if __name__ == "__main__":
    ingest()
