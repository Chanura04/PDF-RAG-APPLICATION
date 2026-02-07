FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make pdf folder
RUN mkdir -p /app/pdfs

CMD ["uvicorn", "main:inngest_client", "--host", "0.0.0.0", "--port", "8000"]
