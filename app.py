import os
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session
import asyncio
import inngest
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "rag-app-secret-key")
UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

inngest_client = inngest.Inngest(app_id="rag_app_2", is_production=False)

def _inngest_api_base() -> str:
    return os.getenv("INNGEST_API_BASE", "http://127.0.0.1:8288/v1")

def fetch_runs(event_id: str) -> list[dict]:
    url = f"{_inngest_api_base()}/events/{event_id}/runs"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json().get("data", [])
    except Exception:
        return []

@app.route("/")
def index():
    # Initialize session state for docs and messages
    if "messages" not in session:
        session["messages"] = []
    if "documents" not in session:
        session["documents"] = []
    return render_template("index.html", documents=session["documents"])


@app.route("/upload", methods=["POST"])
async def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    file_path = UPLOAD_FOLDER / file.filename
    file.save(str(file_path))
    
    # Send ingestion event to Inngest
    await inngest_client.send(
        inngest.Event(
            name="rag/ingest_pdf",
            data={"pdf_path": str(file_path.resolve()), "source_id": file.filename},
        )
    )
    
    doc_info = {
        "name": file.filename,
        "chunks": "Processing...",
        "timestamp": time.strftime("%b %d, %H:%M")
    }
    
    if "documents" not in session:
        session["documents"] = []
    
    if not any(d["name"] == file.filename for d in session["documents"]):
        session["documents"].append(doc_info)
        session.modified = True
        
    return jsonify({"success": True, "doc": doc_info})

@app.route("/query", methods=["POST"])
async def query_pdf():
    data = request.json
    question = data.get("question")
    source_id = data.get("source_id")
    top_k = int(data.get("top_k", 5))
    
    if not question or not source_id:
        return jsonify({"error": "Missing data"}), 400
        
    result = await inngest_client.send(
        inngest.Event(
            name="rag/query_pdf_ai",
            data={"question": question, "top_k": top_k, "source_id": source_id},
        )
    )
    
    return jsonify({"event_id": result[0]})

@app.route("/poll/<event_id>")
def poll_run(event_id):
    runs = fetch_runs(event_id)
    if not runs:
        return jsonify({"status": "Pending"})
    
    run = runs[0]
    status = run.get("status")
    if status in ("Completed", "Succeeded", "Success", "Finished"):
        return jsonify({"status": "Completed", "output": run.get("output") or {}})
    return jsonify({"status": status})

if __name__ == "__main__":
    app.run(debug=True, port=5000)