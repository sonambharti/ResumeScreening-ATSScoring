import os
from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from resume_ats_agent.config.settings import settings
from resume_ats_agent.rag.embedding_service import EmbeddingServiceFactory
from resume_ats_agent.core.exceptions import VectorStoreError
from resume_ats_agent.core.logger import logger

class VectorStoreManager:
    """Manages the local FAISS RAG index (chunking, embedding, indexing, retrieval)."""
    
    def __init__(self):
        self.db_dir = settings.vector_db_dir
        self.embeddings = None
        self.vector_store = None
        
    def _initialize_embeddings(self):
        if not self.embeddings:
            self.embeddings = EmbeddingServiceFactory.get_embeddings()
            
    def add_resumes(self, parsed_resumes: List[Dict[str, Any]]):
        """Add parsed resumes to the vector database.
        
        Args:
            parsed_resumes (List[Dict]): List of dicts, each containing:
                - "filename": str
                - "candidate_name": str
                - "raw_text": str
                
        Raises:
            VectorStoreError: If FAISS indexing fails.
        """
        self._initialize_embeddings()
        
        documents = []
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=150
        )
        
        for resume in parsed_resumes:
            raw_text = resume.get("raw_text", "")
            filename = resume.get("filename", "")
            candidate_name = resume.get("candidate_name", "Unknown")
            
            if not raw_text.strip():
                logger.warning(f"Empty raw text for resume: {filename}. Skipping chunking.")
                continue
                
            metadata = {
                "filename": filename,
                "candidate_name": candidate_name
            }
            
            # Split the text
            chunks = text_splitter.split_text(raw_text)
            logger.info(f"Split resume {filename} into {len(chunks)} text chunks.")
            for chunk in chunks:
                documents.append(Document(page_content=chunk, metadata=metadata))
                
        if not documents:
            logger.warning("No document chunks extracted. Vector store index unmodified.")
            return
            
        logger.info(f"Adding {len(documents)} chunks from {len(parsed_resumes)} resumes to FAISS.")
        
        try:
            # If the index exists locally, load it first to append new documents
            if os.path.exists(os.path.join(self.db_dir, "index.faiss")) and self.vector_store is None:
                self.load_index()
                
            if self.vector_store:
                self.vector_store.add_documents(documents)
            else:
                self.vector_store = FAISS.from_documents(documents, self.embeddings)
                
            self.save_index()
            logger.info("Successfully added documents and updated FAISS index.")
        except Exception as e:
            raise VectorStoreError(f"Failed to index documents in vector store: {str(e)}")
            
    def save_index(self):
        """Save active FAISS index to the local filesystem."""
        if not self.vector_store:
            return
        try:
            os.makedirs(self.db_dir, exist_ok=True)
            self.vector_store.save_local(self.db_dir)
            logger.info(f"Saved FAISS index to '{self.db_dir}'")
        except Exception as e:
            raise VectorStoreError(f"Failed to save FAISS index: {str(e)}")
        
    def load_index(self):
        """Load the FAISS index from the local filesystem."""
        self._initialize_embeddings()
        index_path = os.path.join(self.db_dir, "index.faiss")
        if not os.path.exists(index_path):
            logger.info(f"No existing FAISS index found at '{index_path}' to load.")
            return
            
        try:
            # allow_dangerous_deserialization is required for loading local pickle files in FAISS.
            # Safe because the index files are created and loaded entirely locally.
            self.vector_store = FAISS.load_local(
                self.db_dir, 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
            logger.info(f"Loaded FAISS index from '{self.db_dir}'")
        except Exception as e:
            raise VectorStoreError(f"Failed to load FAISS index: {str(e)}")
            
    def search(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """Perform semantic search on indexed resume chunks.
        
        Args:
            query (str): The search query (e.g. job description or skills query).
            k (int): Number of chunks to retrieve.
            
        Returns:
            List[Tuple[Document, float]]: List of matches (document, distance_score).
            
        Raises:
            VectorStoreError: If search fails.
        """
        self._initialize_embeddings()
        if not self.vector_store:
            if os.path.exists(os.path.join(self.db_dir, "index.faiss")):
                self.load_index()
            else:
                logger.warning("Search requested but FAISS index is empty or does not exist.")
                return []
                
        try:
            # similarity_search_with_score returns list of (Doc, score).
            # Note: For FAISS L2 distance, lower score = higher similarity.
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            raise VectorStoreError(f"FAISS search failed: {str(e)}")
            
    def clear(self):
        """Delete local index files and reset vector store."""
        self.vector_store = None
        try:
            index_file = os.path.join(self.db_dir, "index.faiss")
            pkl_file = os.path.join(self.db_dir, "index.pkl")
            if os.path.exists(index_file):
                os.remove(index_file)
            if os.path.exists(pkl_file):
                os.remove(pkl_file)
            logger.info("FAISS vector store index files cleared.")
        except Exception as e:
            raise VectorStoreError(f"Failed to clear FAISS index: {str(e)}")
