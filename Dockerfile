# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock* README.md ./
COPY src ./src

# Install the project
RUN uv sync --frozen --no-dev

# Create mount point for Claude data
RUN mkdir -p /root/.claude

EXPOSE 8080

# Run the server
CMD ["uv", "run", "ccsinfo", "serve", "--host", "0.0.0.0", "--port", "8080"]
