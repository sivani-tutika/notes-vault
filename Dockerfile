# Base image
FROM python:3.12-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false
WORKDIR /app

# Install system dependencies, NGINX, and Supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy server requirements and install Python packages
COPY requirements-server.txt /app/requirements-server.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements-server.txt

# Remove build dependencies to reduce image size
RUN apt-get purge -y --auto-remove build-essential && rm -rf /var/lib/apt/lists/* || true

# Copy application code
COPY . /app

# Copy NGINX and supervisord configs
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose port 80 (NGINX will handle routing)
EXPOSE 80
ENV PORT=80

# Healthcheck pointing to FastAPI
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s CMD curl -f http://127.0.0.1:8000/health || exit 1

# Start all services with supervisord
CMD ["/usr/bin/supervisord", "-n"]
