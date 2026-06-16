FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api.py .
COPY config.py .
COPY auth.py .
COPY db.py .
COPY mimo.py .
COPY build_mimo_prompt.py .
COPY skill_registry.py .
COPY transcribe.py .
COPY skills/ ./skills/

ENV PORT=8080

CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT}"]