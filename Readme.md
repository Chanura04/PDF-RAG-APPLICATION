PDF-RAG Document Question Answering System
A high-performance Retrieval-Augmented Generation (RAG) system that allows users to upload PDF documents and receive context-aware answers. This project leverages event-driven architecture for seamless document ingestion and state-of-the-art LLMs for precise querying.

🚀 Features
Smart Ingestion: Automatically splits PDF documents into manageable chunks for optimized processing.

Vector Search: Generates high-dimensional embeddings using SentenceTransformers and stores them in Qdrant for lightning-fast retrieval.

Event-Driven Pipeline: Utilizes Inngest and FastAPI to handle background ingestion tasks, ensuring the UI remains responsive.

AI-Powered Answers: Get concise, context-aware responses powered by the NVIDIA DeepSeek LLM.

Interactive UI: A clean, real-time interface built with Streamlit for effortless document management and chatting.

🛠️ Technologies
Language: Python

API Framework: FastAPI

Frontend: Streamlit

Vector Database: Qdrant

Orchestration: Inngest

Embeddings: SentenceTransformers

LLM: NVIDIA DeepSeek

🏁 Getting Started
1. Clone the Repository
Bash
git clone https://github.com/your-username/pdf-rag-app.git
cd pdf-rag-app
2. Install Dependencies
Bash
pip install -r requirements.txt
3. Start the Backend
Bash
uvicorn main:app --host 0.0.0.0 --port 8000
4. Run Inngest Dev Server
For local development and event tracking:

Bash
npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery
5. Launch the Frontend
Bash
streamlit run frontend.py
📖 Usage
Upload: Drop a PDF into the Streamlit sidebar.

Process: The system triggers an event via Inngest to chunk and embed the text.

Query: Once processing is complete, type your question in the chat box.

Insight: The system retrieves the most relevant chunks and generates an answer with cited sources.