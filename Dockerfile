# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false
WORKDIR /app

# Install system dependencies needed for building some Python wheels (temporary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy server requirements (smaller set) and install them
COPY requirements-server.txt /app/requirements-server.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements-server.txt

# Remove build dependencies to reduce image size
RUN apt-get purge -y --auto-remove build-essential && rm -rf /var/lib/apt/lists/* || true

# Copy the rest of the application
COPY . /app

# Expose the port
ENV PORT=8000
EXPOSE 8000

# Healthcheck for orchestration
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s CMD curl -f http://127.0.0.1:8000/health || exit 1

# Ensure the script is executable within the container
RUN chmod +x /app/setup_and_start.sh

# Default command - Use the custom startup script with the flag to start Streamlit
CMD ["/app/setup_and_start.sh", "--start-streamlit"]
