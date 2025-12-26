import logging
from fastapi import FastAPI
import inngest
import inngest.fast_api
from dotenv import load_dotenv
import uuid
import os
import datetime
from data_loader import load_and_chunk_pdf,embed_texts
from vector_db import QdrantStorage
from custom_types import RAGSearchResult,RAGQueryResult,RAGChunkAndSrc,RAGUpsertResult

load_dotenv()

inngest_client=inngest.Inngest(
    app_id="rag_app",
    logger=logging.getLogger("uvicorn"),
    is_production=False,
    serializer=inngest.PydanticSerializer()
)


@inngest_client.create_function(
    fn_id="RAG: Ingest PDF",
    trigger=inngest.TriggerEvent(event="rag/ingest_pdf")
)
async def rag_ingest_pdf(event: inngest.Context):
    def load(event:inngest.Context)->RAGChunkAndSrc:
        pdf_path = event.event.data["pdf_path"]
        source_id = event.event.data.get("source_id", pdf_path)
        chunks = load_and_chunk_pdf(pdf_path)
        return RAGChunkAndSrc(chunks=chunks, src_id=source_id)

    def upsert(chunks_and_src:RAGChunkAndSrc)->RAGQueryResult:
        chunks = chunks_and_src.chunks
        source_id = chunks_and_src.src_id
        vecs = embed_texts(chunks)
        ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source_id}:{i}")) for i in range(len(chunks))]
        payloads = [{"source": source_id, "text": chunks[i]} for i in range(len(chunks))]
        QdrantStorage().upsert(ids, vecs, payloads)
        return RAGUpsertResult(ingested=len(chunks))

    chunks_and_src = await event.step.run("load-and-chunk", lambda: load(event), output_type=RAGChunkAndSrc)
    ingested = await event.step.run("embed-and-upsert", lambda: upsert(chunks_and_src), output_type=RAGUpsertResult)
    return ingested.model_dump()#return a dict


app=FastAPI()

inngest.fast_api.serve(app,inngest_client,[rag_ingest_pdf])







# run qdrant docker db= docker run -d --name qdrant -p 633:6333 -v "$(pwd)/qdrant_storage:/qdrant/storage" qdrant/qdrant



# npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery