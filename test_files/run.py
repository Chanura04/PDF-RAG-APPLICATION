from qdrant_client import QdrantClient
client = QdrantClient("http://localhost:6333")
client.delete_collection("docs")

# from sentence_transformers import SentenceTransformer
# import numpy as np

# # Load your model
# embed_model = SentenceTransformer("BAAI/bge-large-en-v1.5")

# # Sample texts
# texts = [
#     "Artificial intelligence is transforming technology.",
#     "AI is changing the world of tech rapidly.",
#     "The sun rises in the east."
# ]

# # Get embeddings
# embeddings = embed_model.encode(texts, normalize_embeddings=True)

# # Check shape
# print("Embedding shape:", embeddings.shape)  # Should be (3, 1024 for BGE Large)
