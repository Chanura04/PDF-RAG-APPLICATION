import logging
from fastapi import FastAPI
import inngest
import inngest.fast_api
from dotenv import load_dotenv
import uuid
import os
import datetime

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
    return {"Hello": "World"}

app=FastAPI()

inngest.fast_api.serve(app,inngest_client,[rag_ingest_pdf])







# run qdrant docker db= docker run -d --name qdrant -p 633:6333 -v "$(pwd)/qdrant_storage:/qdrant/storage" qdrant/qdrant



# npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery