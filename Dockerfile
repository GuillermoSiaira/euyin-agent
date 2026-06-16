FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server/ ./mcp_server/

ENV MCP_TRANSPORT=streamable-http
ENV PYTHONPATH=/app/mcp_server

CMD ["python", "-m", "mcp_server.server"]
