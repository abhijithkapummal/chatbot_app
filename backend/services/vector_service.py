import faiss
import numpy as np
import pickle
import os
from sentence_transformers import SentenceTransformer
from config import Config

class VectorService:
    # Class-level model instance to avoid re-downloading
    _shared_model = None
    _model_initialized = False
    _model_available = False

    def __init__(self):
        self.dimension = 384  # Dimension of all-MiniLM-L6-v2
        self.index_path = os.path.join(Config.VECTOR_DB_PATH, 'faiss_index')
        self.metadata_path = os.path.join(Config.VECTOR_DB_PATH, 'metadata.pkl')

        # Create directory if it doesn't exist
        os.makedirs(Config.VECTOR_DB_PATH, exist_ok=True)

        # Initialize or load index
        self.index = self._load_or_create_index()
        self.metadata = self._load_metadata()

        # Use shared model instance
        if not VectorService._model_initialized:
            self._init_model()

        self.model = VectorService._shared_model
        self.model_available = VectorService._model_available

    def _init_model(self):
        try:
            print("Initializing SentenceTransformer model (this may take a few minutes on first run)...")
            # Set a longer timeout for model download
            import socket
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(300)  # 5 minutes timeout for model download

            VectorService._shared_model = SentenceTransformer('all-MiniLM-L6-v2')
            VectorService._model_available = True
            VectorService._model_initialized = True

            # Restore original timeout
            socket.setdefaulttimeout(original_timeout)

            print("SentenceTransformer model initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize SentenceTransformer model: {e}")
            print("Vector search will not be available")
            VectorService._model_available = False
            VectorService._model_initialized = True  # Mark as initialized even if failed

    def _load_or_create_index(self):
        if os.path.exists(self.index_path):
            return faiss.read_index(self.index_path)
        else:
            # Create new FAISS index
            index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
            return index

    def _load_metadata(self):
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'rb') as f:
                return pickle.load(f)
        else:
            return []

    def _save_index(self):
        faiss.write_index(self.index, self.index_path)

    def _save_metadata(self):
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)

    def add_document(self, content, metadata):
        try:
            if not self.model_available:
                print("Model not available, cannot add document")
                return False

            # Split content into chunks (simple sentence splitting)
            chunks = self._chunk_text(content)

            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self.model.encode([chunk])
                embedding = embedding / np.linalg.norm(embedding)  # Normalize for cosine similarity

                # Add to index
                self.index.add(embedding.astype('float32'))

                # Store metadata
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'content': chunk,
                    'chunk_id': i
                })
                self.metadata.append(chunk_metadata)

            # Save index and metadata
            self._save_index()
            self._save_metadata()

            return True

        except Exception as e:
            print(f"Error adding document: {e}")
            return False

    def search(self, query, top_k=5):
        try:
            if not self.model_available:
                return []

            if self.index.ntotal == 0:
                return []

            # Generate query embedding
            query_embedding = self.model.encode([query])
            query_embedding = query_embedding / np.linalg.norm(query_embedding)

            # Search
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)

            # Retrieve results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.metadata):
                    result = self.metadata[idx].copy()
                    result['score'] = float(score)
                    results.append(result)

            return results

        except Exception as e:
            print(f"Error searching: {e}")
            return []

    def _chunk_text(self, text, chunk_size=500):
        """Simple text chunking by sentences"""
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk + sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def get_info(self):
        return {
            "total_documents": self.index.ntotal,
            "dimension": self.dimension,
            "metadata_count": len(self.metadata),
            "model_available": self.model_available
        }
