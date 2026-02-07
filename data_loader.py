# # from openai import OpenAI
# from llama_index.readers.file import PDFReader
# from llama_index.core.node_parser import SentenceSplitter
# from llama_index.embeddings.ollama import OllamaEmbedding
#
# from dotenv import load_dotenv
# load_dotenv()
#
# # client = OpenAI()
# #pdf is to long and we divide the pdf into smaller chunks and embedd them and store
#
# # EMBEDDING_MODEL = "text-embedding-3-large"
# EMBEDDING_MODEL = "nomic-embed-text"
#
# embed_model = OllamaEmbedding(
#     model=EMBEDDING_MODEL,
#     base_url="http://localhost:11434",  # default Ollama URL
# )
#
# # EMBEDDING_DIM = 3072
# EMBEDDING_DIM = 768
#
# splitter = SentenceSplitter(chunk_size=1000,chunk_overlap=200)
#
# def load_and_chunk_pdf(path:str):
#     docs=PDFReader().load_data(file=path)
#     texts=[d.text for d in docs if getattr(d,"text",None)]
#     chunks=[]
#     for t in texts:
#         chunks.extend(splitter.split_text(t))
#     return chunks
#
# # def embed_texts(texts:list[str])->list[list[float]]:
# #     response=client.embeddings.create(
# #         input=texts,
# #         model=EMBEDDING_MODEL
# #     )
# #     return [item.embedding for item in response.data]
#
# def embed_texts(texts: list[str]) -> list[list[float]]:
#     embeddings = embed_model.get_text_embedding_batch(texts)
#     return embeddings


import requests
from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter
from sentence_transformers import SentenceTransformer

splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)

# OLLAMA_URL = "http://localhost:11434/v1/embeddings"
# EMBED_MODEL = "mxbai-embed-large"


def load_and_chunk_pdf(path: str):
    docs = PDFReader().load_data(file=path)
    texts = [d.text for d in docs if getattr(d, "text", None)]
    chunks = []
    for t in texts:
        chunks.extend(splitter.split_text(t))
    return chunks

embed_model = SentenceTransformer(
    "BAAI/bge-large-en-v1.5"
     # change to "cpu" if no GPU
)

def embed_texts(texts: list[str]) -> list[list[float]]:
    embeddings = embed_model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True
    )
    return embeddings.tolist()
