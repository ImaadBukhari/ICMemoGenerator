import os
import json
import faiss
import numpy as np
from typing import List, Dict, Any, Tuple
from openai import OpenAI
from sqlalchemy.orm import Session
from backend.db.models import Source, DocumentEmbedding

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class RAGService:
    def __init__(self):
        self.embedding_model = "text-embedding-3-small"
        self.dimension = 1536
        
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a text using OpenAI API"""
        response = client.embeddings.create(
            input=text,
            model=self.embedding_model
        )
        return np.array(response.data[0].embedding, dtype=np.float32)
    
    def create_document_chunks(self, perplexity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create searchable chunks from Perplexity data with source attribution"""
        chunks = []
        
        # Process regular research categories
        if perplexity_data.get("categories"):
            for category, data in perplexity_data["categories"].items():
                if data.get("search_successful") and data.get("content"):
                    content = data["content"]
                    citations = data.get("citations", [])
                    
                    words = content.split()
                    chunk_size = 300
                    
                    for i in range(0, len(words), chunk_size):
                        chunk_text = " ".join(words[i:i + chunk_size])
                        chunks.append({
                            "text": chunk_text,
                            "category": category,
                            "type": "research",
                            "sources": citations,
                            "metadata": {
                                "category_name": category.replace('_', ' ').title(),
                                "chunk_index": i // chunk_size
                            }
                        })
        
        # Process stats categories
        if perplexity_data.get("stats_categories"):
            for category, data in perplexity_data["stats_categories"].items():
                if data.get("search_successful") and data.get("content"):
                    content = data["content"]
                    citations = data.get("citations", [])
                    
                    words = content.split()
                    chunk_size = 300
                    
                    for i in range(0, len(words), chunk_size):
                        chunk_text = " ".join(words[i:i + chunk_size])
                        chunks.append({
                            "text": chunk_text,
                            "category": category,
                            "type": "statistics",
                            "sources": citations,
                            "metadata": {
                                "category_name": category.replace('_', ' ').title(),
                                "chunk_index": i // chunk_size
                            }
                        })
        
        return chunks
    
    def build_faiss_index_from_db(self, db: Session, source_id: int) -> Tuple[faiss.Index, List[Dict[str, Any]]]:
        """Build FAISS index from stored embeddings in database"""
        # Check if embeddings already exist
        existing_embeddings = db.query(DocumentEmbedding).filter(
            DocumentEmbedding.source_id == source_id
        ).all()
        
        if existing_embeddings:
            print(f"✅ Found {len(existing_embeddings)} existing embeddings in database")
            
            # Reconstruct chunks and index from database
            embeddings = []
            chunks = []
            
            for emb in existing_embeddings:
                embeddings.append(np.array(emb.embedding, dtype=np.float32))
                chunks.append({
                    "text": emb.chunk_text,
                    "category": emb.category,
                    "type": emb.chunk_type,
                    "sources": emb.sources or [],
                    "metadata": emb.chunk_metadata or {}  # CHANGED
                })
            
            # Create FAISS index
            embeddings_array = np.array(embeddings, dtype=np.float32)
            index = faiss.IndexFlatL2(self.dimension)
            index.add(embeddings_array)
            
            return index, chunks
        
        return None, []
    
    def build_and_store_embeddings(self, db: Session, source_id: int, chunks: List[Dict[str, Any]]) -> Tuple[faiss.Index, List[Dict[str, Any]]]:
        """Build embeddings and store them in database"""
        if not chunks:
            return None, []
        
        print(f"Building embeddings for {len(chunks)} chunks...")
        
        # Get embeddings for all chunks
        embeddings = []
        for i, chunk in enumerate(chunks):
            if i % 10 == 0:
                print(f"  Processing chunk {i+1}/{len(chunks)}...")
            
            embedding = self.get_embedding(chunk["text"])
            embeddings.append(embedding)
            
            # Store in database
            doc_embedding = DocumentEmbedding(
                source_id=source_id,
                chunk_text=chunk["text"],
                chunk_index=chunk["metadata"].get("chunk_index", 0),
                category=chunk["category"],
                chunk_type=chunk["type"],
                embedding=embedding.tolist(),
                sources=chunk.get("sources", []),
                chunk_metadata=chunk.get("metadata", {})  # CHANGED
            )
            db.add(doc_embedding)
        
        db.commit()
        print(f"✅ Stored {len(chunks)} embeddings in database")
        
        # Create FAISS index
        embeddings_array = np.array(embeddings, dtype=np.float32)
        index = faiss.IndexFlatL2(self.dimension)
        index.add(embeddings_array)
        
        return index, chunks
    
    def retrieve_relevant_context(
        self,
        query: str,
        index: faiss.Index,
        chunks: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve most relevant chunks for a query"""
        if index is None or not chunks:
            return []
        
        query_embedding = self.get_embedding(query)
        query_embedding = np.array([query_embedding], dtype=np.float32)
        
        distances, indices = index.search(query_embedding, top_k)
        
        relevant_chunks = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(chunks):
                chunk = chunks[idx].copy()
                chunk["similarity_score"] = float(1 / (1 + distance))
                relevant_chunks.append(chunk)
        
        return relevant_chunks
    
    def format_context_with_sources(self, relevant_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format retrieved context with source attribution"""
        context_text = []
        all_sources = []
        source_map = {}
        
        for i, chunk in enumerate(relevant_chunks):
            category = chunk["metadata"]["category_name"]
            chunk_type = chunk["type"].title()
            text = chunk["text"]
            sources = chunk.get("sources", [])
            
            citation_num = i + 1
            context_text.append(f"[{citation_num}] {category} ({chunk_type}):\n{text}\n")
            
            if sources:
                source_map[citation_num] = sources
                all_sources.extend(sources)
        
        unique_sources = list(set(all_sources))
        
        return {
            "context": "\n".join(context_text),
            "sources": unique_sources,
            "source_map": source_map,
            "num_chunks": len(relevant_chunks)
        }

# Global RAG service instance
rag_service = RAGService()

def build_company_knowledge_base(db: Session, source_id: int) -> Tuple[faiss.Index, List[Dict[str, Any]]]:
    """Build FAISS index for a company's data - use cached embeddings if available"""
    
    # First, try to load from database
    index, chunks = rag_service.build_faiss_index_from_db(db, source_id)
    
    if index is not None:
        return index, chunks
    
    # If no cached embeddings, build new ones
    print("No cached embeddings found, building new ones...")
    source = db.query(Source).filter(Source.id == source_id).first()
    
    if not source or not source.perplexity_data:
        return None, []
    
    chunks = rag_service.create_document_chunks(source.perplexity_data)
    index, chunks = rag_service.build_and_store_embeddings(db, source_id, chunks)
    
    return index, chunks

def retrieve_context_for_section(
    section_key: str,
    section_prompt: str,
    index: faiss.Index,
    chunks: List[Dict[str, Any]],
    company_name: str,
    top_k: int = 8
) -> Dict[str, Any]:
    """Retrieve relevant context for a specific memo section"""
    
    query = f"{company_name} {section_key.replace('_', ' ')}: {section_prompt[:200]}"
    relevant_chunks = rag_service.retrieve_relevant_context(query, index, chunks, top_k)
    formatted_context = rag_service.format_context_with_sources(relevant_chunks)
    
    return formatted_context