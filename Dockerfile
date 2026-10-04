# Stage 1: Builder - install dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Runtime - lean final image
FROM python:3.12-slim

LABEL org.opencontainers.image.title="Framework Magnifier"
LABEL org.opencontainers.image.description="AI-powered cross-platform system monitor using Gemma-4"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy source
COPY magnifier.py .

# psutil needs procfs access - run as root inside container (safe in Docker context)
# Pass your key via: docker run -e GEMINI_API_KEY=your_key ...
ENV MAGNIFIER_MODEL="gemma-4"

ENTRYPOINT ["python", "magnifier.py"]
CMD []
