FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy application code
COPY backend ./backend/

# Sanity check: fail early if wrong Python version
RUN python -c "import sys; assert sys.version_info >= (3,11), f'Python version is {sys.version}'"

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Start the app
CMD exec uvicorn backend.app:app --host 0.0.0.0 --port 8080
