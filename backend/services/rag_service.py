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
        
    def get_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Get embeddings for multiple texts in one API call (much faster!)"""
        response = client.embeddings.create(
            input=texts,
            model=self.embedding_model
        )
        return [np.array(item.embedding, dtype=np.float32) for item in response.data]
    
    def create_document_chunks(self, perplexity_data: Dict[str, Any], affinity_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Create searchable chunks from Perplexity data AND Affinity/Crunchbase data with source attribution"""
        chunks = []
        
        # INCREASED CHUNK SIZE for efficiency
        chunk_size = 800
        
        # Process Affinity/Crunchbase data FIRST
        if affinity_data:
            crunchbase_text_parts = []
            
            # Extract relevant fields from Affinity
            key_fields = [
                ('name', 'Company Name'),
                ('stage', 'Stage'),
                ('industry', 'Industry'),
                ('description', 'Description'),
                ('website', 'Website'),
                ('funding_stage', 'Funding Stage'),
                ('last_funding_amount', 'Last Funding Amount'),
                ('total_funding', 'Total Funding Raised'),
                ('valuation', 'Valuation'),
                ('employees', 'Employee Count'),
                ('headquarters', 'Headquarters'),
                ('founded_date', 'Founded Date'),
                ('investors', 'Investors'),
                ('ceo', 'CEO'),
                ('founders', 'Founders')
            ]
            
            for field_key, field_name in key_fields:
                if field_key in affinity_data and affinity_data[field_key]:
                    crunchbase_text_parts.append(f"{field_name}: {affinity_data[field_key]}")
            
            # Create ONE chunk for all Crunchbase data
            if crunchbase_text_parts:
                crunchbase_text = "\n".join(crunchbase_text_parts)
                chunks.append({
                    "text": crunchbase_text,
                    "category": "crunchbase_data",
                    "type": "crm",
                    "sources": ["Crunchbase (via Affinity CRM)"],  # Single source attribution
                    "metadata": {
                        "category_name": "CRM Data",
                        "chunk_index": 0
                    }
                })
        
        # Process regular Perplexity research categories
        if perplexity_data.get("categories"):
            for category, data in perplexity_data["categories"].items():
                if data.get("search_successful") and data.get("content"):
                    content = data["content"]
                    citations = data.get("citations", [])
                    
                    words = content.split()
                    
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
        existing_embeddings = db.query(DocumentEmbedding).filter(
            DocumentEmbedding.source_id == source_id
        ).all()
        
        if existing_embeddings:
            print(f"✅ Found {len(existing_embeddings)} existing embeddings in database")
            
            embeddings = []
            chunks = []
            
            for emb in existing_embeddings:
                embeddings.append(np.array(emb.embedding, dtype=np.float32))
                chunks.append({
                    "text": emb.chunk_text,
                    "category": emb.category,
                    "type": emb.chunk_type,
                    "sources": emb.sources or [],
                    "metadata": emb.chunk_metadata or {}
                })
            
            embeddings_array = np.array(embeddings, dtype=np.float32)
            index = faiss.IndexFlatL2(self.dimension)
            index.add(embeddings_array)
            
            return index, chunks
        
        return None, []
    
    def build_and_store_embeddings(self, db: Session, source_id: int, chunks: List[Dict[str, Any]]) -> Tuple[faiss.Index, List[Dict[str, Any]]]:
        """Build embeddings and store them in database - BATCHED FOR SPEED"""
        if not chunks:
            return None, []
        
        print(f"Building embeddings for {len(chunks)} chunks using batch processing...")
        
        # Extract all texts for batch processing
        texts = [chunk["text"] for chunk in chunks]
        
        # Get ALL embeddings in batches of 100 (OpenAI limit)
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"  Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1} ({len(batch)} chunks)...")
            batch_embeddings = self.get_embeddings_batch(batch)
            all_embeddings.extend(batch_embeddings)
        
        print(f"✅ Generated {len(all_embeddings)} embeddings")
        
        # Store in database
        print("Storing embeddings in database...")
        for i, (chunk, embedding) in enumerate(zip(chunks, all_embeddings)):
            doc_embedding = DocumentEmbedding(
                source_id=source_id,
                chunk_text=chunk["text"],
                chunk_index=chunk["metadata"].get("chunk_index", 0),
                category=chunk["category"],
                chunk_type=chunk["type"],
                embedding=embedding.tolist(),
                sources=chunk.get("sources", []),
                chunk_metadata=chunk.get("metadata", {})
            )
            db.add(doc_embedding)
            
            if (i + 1) % 50 == 0:
                print(f"  Stored {i + 1}/{len(chunks)} embeddings...")
        
        db.commit()
        print(f"✅ Stored {len(chunks)} embeddings in database")
        
        # Create FAISS index
        embeddings_array = np.array(all_embeddings, dtype=np.float32)
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
        
        query_embedding = self.get_embeddings_batch([query])[0]
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
        """Format retrieved context with source attribution and deduplication"""
        context_text = []
        all_sources = []
        source_map = {}
        seen_sources = {}  # Track unique sources with their citation numbers
        citation_counter = 1
        
        for chunk in relevant_chunks:
            category = chunk["metadata"]["category_name"]
            chunk_type = chunk["type"].title()
            text = chunk["text"]
            sources = chunk.get("sources", [])
            
            # Deduplicate sources - assign same number to identical sources
            chunk_citations = []
            for source in sources:
                if source not in seen_sources:
                    seen_sources[source] = citation_counter
                    all_sources.append(source)
                    citation_counter += 1
                chunk_citations.append(seen_sources[source])
            
            # Format citation numbers
            if chunk_citations:
                citation_str = "[" + ", ".join(map(str, sorted(set(chunk_citations)))) + "]"
            else:
                citation_str = ""
            
            context_text.append(f"{citation_str} {category} ({chunk_type}):\n{text}\n")
            
            if sources:
                for source in sources:
                    source_num = seen_sources[source]
                    if source_num not in source_map:
                        source_map[source_num] = source
        
        return {
            "context": "\n".join(context_text),
            "sources": all_sources,  # Deduplicated list
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
    
    # Pass BOTH Perplexity and Affinity data to create chunks
    chunks = rag_service.create_document_chunks(
        source.perplexity_data,
        affinity_data=source.affinity_data  # ADD THIS
    )
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