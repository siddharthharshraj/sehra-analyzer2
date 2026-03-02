FROM python:3.11-slim

WORKDIR /app

# System deps: build tools + WeasyPrint rendering libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optional: install Surya OCR for scanned PDF support
ARG SCANNED_PDF_SUPPORT=false
RUN if [ "$SCANNED_PDF_SUPPORT" = "true" ]; then \
    pip install --no-cache-dir surya-ocr; \
    fi

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:${PORT:-8501}/_stcore/health || exit 1

ENTRYPOINT ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false"]
