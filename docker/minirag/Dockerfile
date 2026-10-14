FROM ghcr.io/astral-sh/uv:0.7.2-python3.12-bookworm

WORKDIR /app

# Install additional system dependencies or lxml and other packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libavif-dev pkg-config \
    libjpeg-dev \
    gcc unzip zip \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*


COPY src/requirements.txt .

RUN uv pip install -r requirements.txt --system

COPY src/ .

# Create directory structure for Alembic
RUN mkdir -p models/db_schemes/minirag

COPY docker/minirag/alembic.ini /app/models/db_schemes/minirag

COPY docker/minirag/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh


ENTRYPOINT [ "/entrypoint.sh" ]

# Command to run the application
# uvicorn main:app --reload --host 0.0.0.0 --port 5000
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4" ]



