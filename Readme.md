# PDF-RAG Document Question Answering System

A **Retrieval-Augmented Generation (RAG)** system for PDFs that allows you to upload documents and ask questions, retrieving context-aware answers from the content.

**Technologies:** Python, FastAPI, Streamlit, Qdrant, SentenceTransformers, NVIDIA DeepSeek, Inngest

---

## Features

- Upload PDF documents and automatically split them into chunks for processing.
- Generate embeddings for chunks using **SentenceTransformers** and store them in **Qdrant** vector database.
- Event-driven ingestion and query handling using **FastAPI** and **Inngest** triggers.
- Ask questions about your PDFs and get concise, context-aware answers powered by **NVIDIA DeepSeek LLM**.
- User-friendly **Streamlit interface** for uploading PDFs and querying the system in real-time.

---

[![Watch the video](https://img.youtube.com/vi/kq1CdeekXIA/0.jpg)](https://www.youtube.com/watch?v=kq1CdeekXIA)


---

## Getting Started

1. **Clone the repository**

```bash
git clone https://github.com/Chanura04/PDF-RAG-APPLICATION.git
cd pdf-rag-app
```

2. Install Dependencies
```bash
pip install -r requirements.txt
```

3. Start the Backend
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

4. Run Inngest Dev Server
For local development and event tracking:
```bash
npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery
```

5. Launch the Frontend
```bash
streamlit run frontend.py
```

📖 Usage Guide
```

📥 1. Upload a PDF
  Upload your PDF using the sidebar in the Streamlit UI.

⚙️ 2. Automated Processing
  The system will:
  - Extract text
  - Chunk it
  - Generate embeddings
  - Store vectors in Qdrant (Image/loader shows progress)

💬 3. Ask Questions
    Use the chat box to ask anything about your PDF.

🔍 4. Get Contextual Insights
  The system will:
    - Retrieve the most similar chunks
    - Generate a response using DeepSeek
    - Provide citations referencing specific PDF sections
```
