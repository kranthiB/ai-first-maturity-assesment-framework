
FROM python:3.11-slim

# Install system dependencies required for Chromium/Playwright
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgtk-3-0 \
    libasound2 \
    libgbm1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxshmfence1 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-icu0 \
    libwebp-dev \
    libjpeg-dev \
    libvpx-dev \
    libopus-dev \
    libwoff1 \
    libgl1 \
    libgles2 \
    libcurl4 \
    libx11-xcb1 \
    libxext6 \
    libxi6 \
    libxtst6 \
    libxss1 \
    libxinerama1 \
    libatspi2.0-0 \
    libappindicator3-1 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Add non-root user for Chromium/Playwright
RUN useradd -m chrome && mkdir -p /home/chrome && chown -R chrome:chrome /home/chrome
USER chrome

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Install Playwright browsers and dependencies
RUN python -m playwright install

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
