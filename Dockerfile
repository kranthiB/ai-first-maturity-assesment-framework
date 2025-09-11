FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data/exports static/uploads backups instance

# Expose port
EXPOSE 5000

# Environment variables
ENV FLASK_APP=run.py \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:///instance/app_dev.db

# Run database setup and start the application
CMD python scripts/setup_database.py && python run.py
