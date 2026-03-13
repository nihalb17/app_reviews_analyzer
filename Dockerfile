# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    fonts-unifont \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
# Skip playwright install-deps as we manually installed required packages above

# Copy the entire project
COPY . .

# Create necessary directories
RUN mkdir -p backend/Phase_1_Data_Ingestion_Layer/data \
    backend/Phase_2_Theme_Extraction_Classification/data \
    backend/Phase_3_Insight_Generation/data \
    backend/Phase_4_Report_Generation/output \
    backend/Phase_4_Report_Generation/data \
    backend/backend_data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8001

# Start command
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8001"]
