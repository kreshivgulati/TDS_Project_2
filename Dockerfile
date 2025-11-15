# ----------------------------
# 1. Base Image
# ----------------------------
FROM python:3.11-slim

# ----------------------------
# 2. System Dependencies
# ----------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libatk1.0-data \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------
# 3. Set Work Directory
# ----------------------------
WORKDIR /app

# ----------------------------
# 4. Copy Dependencies First
# ----------------------------
COPY requirements.txt .

# ----------------------------
# 5. Install Python Dependencies
# ----------------------------
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------
# 6. Install Playwright Browsers
# ----------------------------
RUN playwright install --with-deps chromium

# ----------------------------
# 7. Copy Project Files
# ----------------------------
COPY . .

# ----------------------------
# 8. Expose Port
# ----------------------------
EXPOSE 8000

# ----------------------------
# 9. Start FastAPI Server
# ----------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
