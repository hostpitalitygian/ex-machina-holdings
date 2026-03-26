FROM python:3.11-slim

# Non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Install deps first — leverages Docker layer cache on rebuilds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Drop privileges
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Healthcheck — Docker marks container unhealthy if /health stops responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]
