import asyncio
from pathlib import Path
import time

import streamlit as st
import inngest
from dotenv import load_dotenv
import os
import requests

load_dotenv()

st.set_page_config(
    page_title="RAG PDF Assistant", 
    page_icon="📚", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    
    .main-header {
        font-size: 18px;
        font-weight: 700;
        text-align: center;
 
      
 
        color: white;
        font-size: 28px;
    }
    .subtitle {
        color: white;
        font-size: 18px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .upload-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    .query-section {
        background: #f0f7ff;
        padding: 2rem;
        border-radius: 12px;
    }
    .success-badge {
        background: #d4edda;
        color: #155724;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .source-item {
        background: #fff;
        padding: 0.75rem;
        border-left: 3px solid #667eea;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    div[data-testid="stFileUploader"] {
        border: 2px dashed #667eea;
        border-radius: 8px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_inngest_client() -> inngest.Inngest:
    return inngest.Inngest(app_id="rag_app_2", is_production=False)


def save_uploaded_pdf(file) -> Path:
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / file.name
    file_bytes = file.getbuffer()
    file_path.write_bytes(file_bytes)
    return file_path


async def send_rag_ingest_event(pdf_path: Path) -> None:
    client = get_inngest_client()
    await client.send(
        inngest.Event(
            name="rag/ingest_pdf",
            data={
                "pdf_path": str(pdf_path.resolve()),
                "source_id": pdf_path.name,
            },
        )
    )


def _inngest_api_base() -> str:
    return os.getenv("INNGEST_API_BASE", "http://127.0.0.1:8288/v1")


def fetch_runs(event_id: str) -> list[dict]:
    url = f"{_inngest_api_base()}/events/{event_id}/runs"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])


def wait_for_run_output(event_id: str, timeout_s: float = 120.0, poll_interval_s: float = 0.5) -> dict:
    start = time.time()
    last_status = None
    while True:
        runs = fetch_runs(event_id)
        if runs:
            run = runs[0]
            status = run.get("status")
            last_status = status or last_status
            if status in ("Completed", "Succeeded", "Success", "Finished"):
                return run.get("output") or {}
            if status in ("Failed", "Cancelled"):
                raise RuntimeError(f"Function run {status}")
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Timed out waiting for run output (last status: {last_status})")
        time.sleep(poll_interval_s)


async def send_rag_query_event(question: str, top_k: int, source_id: str) -> None:
    client = get_inngest_client()
    result = await client.send(
        inngest.Event(
            name="rag/query_pdf_ai",
            data={
                "question": question,
                "top_k": top_k,
                "source_id": source_id,
            },
        )
    )
    return result[0]


# Header
st.markdown('<p class="main-header" style="font-size: 38px; text-align: center;">📚 RAG PDF Assistant</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Upload your documents and ask questions powered by AI</p>', unsafe_allow_html=True)

# Upload Section
# st.markdown('<div class="upload-section">', unsafe_allow_html=True)
st.subheader("📤 Step 1: Upload PDF")
uploaded = st.file_uploader(
    "Choose a PDF file to analyze",
    type=["pdf"],
    accept_multiple_files=False,
    help="Upload a PDF document to make it searchable"
)

if uploaded is not None:
    with st.spinner("🔄 Processing your document..."):
        path = save_uploaded_pdf(uploaded)
        asyncio.run(send_rag_ingest_event(path))
        st.session_state["last_uploaded"] = path.name
        time.sleep(0.3)
    
    st.markdown(
        f'<div class="success-badge">✅ Successfully ingested: <strong>{path.name}</strong></div>',
        unsafe_allow_html=True
    )
st.markdown('</div>', unsafe_allow_html=True)

# Query Section
# st.markdown('<div class="query-section">', unsafe_allow_html=True)
st.subheader("💬 Step 2: Ask Questions")

# Check if a file has been uploaded
if "last_uploaded" in st.session_state:
    st.caption(f"📄 Currently querying: **{st.session_state['last_uploaded']}**")
else:
    st.info("👆 Please upload a PDF first before asking questions")

col1, col2 = st.columns([3, 1])

with col1:
    question = st.text_input(
        "Your question",
        placeholder="e.g., What is the main topic of this document?",
        label_visibility="collapsed"
    )

with col2:
    top_k = st.number_input(
        "Chunks",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        help="Number of relevant chunks to retrieve"
    )

ask_button = st.button("🔍 Get Answer", type="primary", use_container_width=True)

if ask_button and question.strip():
    if "last_uploaded" not in st.session_state:
        st.error("⚠️ Please upload a PDF first!")
    else:
        with st.spinner("🤔 Analyzing your document and generating answer..."):
            source_id = st.session_state.get("last_uploaded")
            try:
                event_id = asyncio.run(send_rag_query_event(question.strip(), int(top_k), source_id))
                output = wait_for_run_output(event_id)
                answer = output.get("answer", "")
                sources = output.get("sources", [])

                st.markdown("---")
                st.subheader("💡 Answer")
                if answer:
                    st.markdown(answer)
                else:
                    st.warning("No answer generated")
                
                if sources:
                    st.markdown("---")
                    st.subheader("📑 Sources")
                    for s in sources:
                        st.markdown(f'<div class="source-item">{s}</div>', unsafe_allow_html=True)
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)