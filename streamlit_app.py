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
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Inngest helpers ──────────────────────────────────────────────────────────

@st.cache_resource
def get_inngest_client() -> inngest.Inngest:
    return inngest.Inngest(app_id="rag_app_2", is_production=False)


def save_uploaded_pdf(file) -> Path:
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / file.name
    file_path.write_bytes(file.getbuffer())
    return file_path


async def send_rag_ingest_event(pdf_path: Path) -> None:
    client = get_inngest_client()
    await client.send(
        inngest.Event(
            name="rag/ingest_pdf",
            data={"pdf_path": str(pdf_path.resolve()), "source_id": pdf_path.name},
        )
    )


def _inngest_api_base() -> str:
    return os.getenv("INNGEST_API_BASE", "http://127.0.0.1:8288/v1")


def fetch_runs(event_id: str) -> list[dict]:
    url = f"{_inngest_api_base()}/events/{event_id}/runs"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json().get("data", [])


def wait_for_run_output(
    event_id: str, timeout_s: float = 120.0, poll_interval_s: float = 0.5
) -> dict:
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
            raise TimeoutError(f"Timed out waiting for run (last status: {last_status})")
        time.sleep(poll_interval_s)


async def send_rag_query_event(question: str, top_k: int, source_id: str):
    client = get_inngest_client()
    result = await client.send(
        inngest.Event(
            name="rag/query_pdf_ai",
            data={"question": question, "top_k": top_k, "source_id": source_id},
        )
    )
    return result[0]


# ── Session state ────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []       # [{role, content, sources}]
if "documents" not in st.session_state:
    st.session_state.documents = []      # [{name, chunks, timestamp}]
if "active_doc" not in st.session_state:
    st.session_state.active_doc = None


# ── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📚 RAG PDF Assistant")
    st.markdown(
        "Upload PDF documents and ask questions powered by AI retrieval."
    )

    st.divider()

    # ── Upload
    st.header("📤 Upload Document")
    uploaded = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        accept_multiple_files=False,
    )

    if uploaded is not None:
        already = any(d["name"] == uploaded.name for d in st.session_state.documents)
        if not already:
            with st.spinner("⏳ Ingesting document…"):
                path = save_uploaded_pdf(uploaded)
                asyncio.run(send_rag_ingest_event(path))
                time.sleep(0.3)
            st.session_state.documents.append(
                {
                    "name": uploaded.name,
                    "chunks": 5,  # placeholder; replace with real count if API returns it
                    "timestamp": time.strftime("%b %d, %H:%M"),
                }
            )
            st.session_state.active_doc = uploaded.name
            st.session_state.messages = []
            st.success(f"✅ Ingested: **{uploaded.name}**")
            st.rerun()

    st.divider()

    # ── Document list
    st.header("📄 Documents")
    if st.session_state.documents:
        for doc in st.session_state.documents:
            is_active = doc["name"] == st.session_state.active_doc
            label = f"{'▶ ' if is_active else ''}{doc['name']}"
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"doc_{doc['name']}", use_container_width=True, type=btn_type):
                if not is_active:
                    st.session_state.active_doc = doc["name"]
                    st.session_state.messages = []
                    st.rerun()
            st.caption(f"🧩 {doc['chunks']} chunks  ·  🕐 {doc['timestamp']}")
    else:
        st.info("No documents uploaded yet.")

    st.divider()

    # ── Settings
    st.header("⚙️ Settings")
    top_k = st.number_input(
        "Chunks to retrieve",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        help="How many document chunks to retrieve per query",
    )

    st.divider()

    # ── How it works
    st.header("ℹ️ How it works")
    st.markdown(
        """
        1. **Upload** a PDF document  
        2. The document is **chunked & indexed** automatically  
        3. **Ask questions** in the chat  
        4. Relevant chunks are **retrieved** and an AI answer is generated  
        """
    )

    st.divider()

    if st.session_state.messages:
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


# ── MAIN CHAT AREA ───────────────────────────────────────────────────────────

active = st.session_state.active_doc

if active:
    st.title(f"💬 Chat — {active}")
else:
    st.title("💬 RAG PDF Chat")

st.markdown("Ask any question about your document and get AI-powered answers!")

# Show existing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("📑 Sources", expanded=False):
                for s in message["sources"]:
                    st.markdown(f"- {s}")

# Guard: no doc selected
if not active:
    st.info("👈 Upload a PDF in the sidebar to get started.")
    st.stop()

# Chat input
if user_query := st.chat_input("Ask a question about your document…"):
    # Show user message
    st.session_state.messages.append(
        {"role": "user", "content": user_query, "sources": []}
    )
    with st.chat_message("user"):
        st.markdown(user_query)

    # Generate answer
    with st.chat_message("assistant"):
        with st.spinner("🔍 Retrieving relevant chunks and generating answer…"):
            status_placeholder = st.empty()
            status_placeholder.info("⏳ Querying document…")
            try:
                event_id = asyncio.run(
                    send_rag_query_event(user_query.strip(), int(top_k), active)
                )
                output = wait_for_run_output(event_id)
                answer = output.get("answer", "No answer was generated.")
                sources = output.get("sources", [])
            except Exception as e:
                answer = f"❌ Error: {str(e)}"
                sources = []
            status_placeholder.empty()

        st.markdown(answer)
        if sources:
            with st.expander("📑 Sources", expanded=False):
                for s in sources:
                    st.markdown(f"- {s}")

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )