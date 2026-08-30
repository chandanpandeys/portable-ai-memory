FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY memory_os ./memory_os
RUN pip install --no-cache-dir '.[mcp]'
ENV MEMORY_DB_PATH=/data/memory.sqlite
EXPOSE 8000
CMD ["python", "-m", "memory_os.mcp_server"]
