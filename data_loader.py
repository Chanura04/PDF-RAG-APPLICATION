import requests
from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter
from sentence_transformers import SentenceTransformer

# splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)
splitter = SentenceSplitter(chunk_size=100, chunk_overlap=50)


def load_and_chunk_pdf(path: str):
    docs = PDFReader().load_data(file=path)
    texts = [d.text for d in docs if getattr(d, "text", None)]
    chunks = []
    for t in texts:
        chunks.extend(splitter.split_text(t))
    return chunks

embed_model = SentenceTransformer(
    "BAAI/bge-large-en-v1.5"
     
)

def embed_texts(texts: list[str]) -> list[list[float]]:
    embeddings = embed_model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True
    )
    return embeddings.tolist()
