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
    app_id="rag_app_2",
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
        # source_id = event.event.data.get("source_id", pdf_path)
        source_id = event.event.data["source_id"]

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


@inngest_client.create_function(
    fn_id="RAG: Query PDF",
    trigger=inngest.TriggerEvent(event="rag/query_pdf_ai")



)
async def rag_query_pdf_ai(ctx: inngest.Context):
    def _search(question: str, top_k: int,source_id: str ) -> RAGSearchResult:
        query_vec = embed_texts([question])[0]#TAKE FIRST RESULT
        store = QdrantStorage()
        found = store.search(query_vec, top_k,source_id=source_id)
        return RAGSearchResult(contexts=found["contexts"], sources=found["sources"],source_id=source_id)

    question = ctx.event.data["question"]
    top_k = int(ctx.event.data.get("top_k", 5))
    source_id = ctx.event.data.get("source_id")

    # found = await ctx.step.run("embed-and-search", lambda: _search(question, top_k), output_type=RAGSearchResult)
    found = await ctx.step.run(
        "embed-and-search",
        lambda: _search(question, top_k, source_id),
        output_type=RAGSearchResult
    )

    context_block = "\n\n".join(f"- {c}" for c in found.contexts)
    # user_content = (
    #     "Use the following context to answer the question.\n\n"
    #     f"Context:\n{context_block}\n\n"
    #     f"Question: {question}\n"
    #     "Answer concisely using the context above."
    # )
    user_content = (
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n\n"
        "Final answer only:"
    )

    # import httpx
    #
    # OLLAMA_CHAT_URL = "http://localhost:11434/v1/chat/completions"
    # OLLAMA_LLM = "deepseek-r1:8b"  # or "deepseek-r1:8b"  llama3.2:3b
    #
    #
    # async with httpx.AsyncClient(timeout=300) as client:
    #         response = await client.post(
    #             OLLAMA_CHAT_URL,
    #             json={
    #                 "model": OLLAMA_LLM,
    #                 "messages": [
    #                     {
    #                         "role": "system",
    #                         "content": "You answer questions using only the provided context."
    #                     },
    #                     {
    #                         "role": "user",
    #                         "content": user_content
    #                     }
    #                 ],
    #                 "temperature": 0.2,
    #                 "max_tokens": 1024
    #             }
    #         )
    #         response.raise_for_status()
    #         data = response.json()
    #         answer = data["choices"][0]["message"]["content"].strip()
    #         return {"answer": answer, "sources": found.sources, "num_contexts": len(found.contexts)}

    from openai import OpenAI

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key="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"
    )

    completion = client.chat.completions.create(
        model="deepseek-ai/deepseek-v3.2",
        messages=[
                {
                "role": "user",
                "content": (
    "You must answer using ONLY the provided context.\n"
    "Return ONLY the final answer.\n"
    "DO NOT explain your reasoning.\n"
    "DO NOT show thoughts, analysis, or commentary.\n"
    "DO NOT restate the question.\n"
    "Answer in 1–2 concise sentences."
)

                },
                {
                      "role": "user",
                      "content": user_content
                }
                ],
        temperature=1,
        top_p=0.95,
        max_tokens=8192,
        extra_body={"chat_template_kwargs": {"thinking": True}},
        stream=True
    )

    # for chunk in completion:
    #     if not getattr(chunk, "choices", None):
    #         continue
    #     reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
    #     if reasoning:
    #         print(reasoning, end="")
    #     if chunk.choices[0].delta.content is not None:
    #         print(chunk.choices[0].delta.content, end="")
    answer_parts = []
    for chunk in completion:
        if not getattr(chunk, "choices", None):
            continue

        reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
        if reasoning:
            answer_parts.append(reasoning)

        if chunk.choices[0].delta.content is not None:
            answer_parts.append(chunk.choices[0].delta.content)

    answer = "".join(answer_parts).strip()
    return {"answer": answer, "sources": found.sources, "num_contexts": len(found.contexts)}

    # adapter = ai.openai.Adapter(
    #     auth_key=os.getenv("OPENAI_API_KEY"),
    #     model="gpt-4o-mini"
    # )
    #
    # res = await ctx.step.ai.infer(
    #     "llm-answer",
    #     adapter=adapter,
    #     body={
    #         "max_tokens": 1024,
    #         "temperature": 0.2,
    #         "messages": [
    #             {"role": "system", "content": "You answer questions using only the provided context."},
    #             {"role": "user", "content": user_content}
    #         ]
    #     }
    # )

    # answer = res["choices"][0]["message"]["content"].strip()
    # return {"answer": answer, "sources": found.sources, "num_contexts": len(found.contexts)}

app = FastAPI()

inngest.fast_api.serve(app, inngest_client, [rag_ingest_pdf, rag_query_pdf_ai])








# run qdrant docker db= docker run -d --name qdrant -p 633:6333 -v "$(pwd)/qdrant_storage:/qdrant/storage" qdrant/qdrant
# docker run -p 6333:6333 qdrant/qdrant


#ingest web-    npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery


#uv run uvicorn main:app