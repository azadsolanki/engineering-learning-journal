FROM python:3.11-slim

WORKDIR /app

# Install kubectl
RUN apt-get update && apt-get install -y curl ca-certificates && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    apt-get purge -y --auto-remove curl && rm -rf /var/lib/apt/lists/* kubectl

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY phase1-rag/ ./phase1-rag/
COPY phase2-langgraph/ ./phase2-langgraph/
COPY phase3-kubernetes/ ./phase3-kubernetes/

EXPOSE 8000

CMD ["uvicorn", "phase3-kubernetes.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
