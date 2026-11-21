# Build from the repository root:  docker build -f services/python/Dockerfile -t aie-service .
FROM python:3.12-slim
WORKDIR /app
COPY services/python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY aie/ aie/
COPY prompts/ prompts/
COPY data/ data/
COPY services/ services/
ENV AIE_ENV=production
ENV OLLAMA_URL=http://host.docker.internal:11434
EXPOSE 8000
CMD ["uvicorn", "services.python.app:app", "--host", "0.0.0.0", "--port", "8000"]
