# Base Image
FROM python:3.11-slim

# Install system dependencies for WeasyPrint/PDF generation
# (Required for generate_test_report "pdf" format)
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libpango1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Set Working Directory
WORKDIR /app

# Copy Requirements first (Docker Cache Layering)
COPY requirements.txt .

# Install Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Source Code
COPY src/ src/
COPY pyproject.toml .
# Copy Manual (Optional, but good for reference)
COPY MCP_SERVER_MANUAL.txt .

# Setup Data Volume
ENV DATA_DIR=/app/data
RUN mkdir -p /app/data
VOLUME /app/data

# Expose Port (for SSE)
EXPOSE 8000

# Set Transport Mode
ENV MCP_TRANSPORT=sse

# Run Command
CMD ["python", "-m", "src.main"]
