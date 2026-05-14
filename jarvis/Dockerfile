FROM python:3.12-slim

WORKDIR /app

# Install system deps for Playwright and Node.js
RUN apt-get update && apt-get install -y \
    curl wget gnupg ca-certificates \
    nodejs npm \
    libnss3 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (for web browsing feature)
RUN playwright install chromium --with-deps 2>/dev/null || true

# Frontend build
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm ci --silent
COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# Copy all app files
COPY . .

# Create data directory
RUN mkdir -p data

EXPOSE 8340

CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8340"]
