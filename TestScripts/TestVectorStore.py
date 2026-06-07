

import os
import sys
import traceback
from dotenv import load_dotenv
# Add project root to path
sys.path.append(r"e:\Assignments\Resume Screening - ATS Scoring Platform")
def test():
    # Load env variables (if any) or read from .env.example/active env
    load_dotenv()
    
    from resume_ats_agent.config.settings import settings
    from resume_ats_agent.rag.embedding_service import EmbeddingServiceFactory
    from langchain_core.documents import Document
    from langchain_community.vectorstores import FAISS
    
    print("Embedding Provider:", settings.embedding_provider)
    print("Embedding Model Name:", settings.embedding_model_name)
    print("OpenAI Key Configured:", bool(settings.openai_api_key))
    print("Gemini Key Configured:", bool(settings.gemini_api_key))
    
    try:
        print("\nInitializing embeddings...")
        embeddings = EmbeddingServiceFactory.get_embeddings()
        print("Embeddings initialized successfully!")
        
        # Test document
        docs = [Document(page_content="Test document content to verify indexing works properly.")]
        print("\nCreating FAISS index from documents...")
        db = FAISS.from_documents(docs, embeddings)
        print("FAISS index created successfully!")
        
        print("\nSaving FAISS index locally...")
        os.makedirs("./data/test_vector_db", exist_ok=True)
        db.save_local("./data/test_vector_db")
        print("FAISS index saved successfully!")
    except Exception as e:
        print("\n--- ERROR CAUGHT ---")
        traceback.print_exc()
if __name__ == "__main__":
    test()