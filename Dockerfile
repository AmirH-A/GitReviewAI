FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create repo directory
RUN mkdir -p /repo

# Set environment variables
ENV PYTHONPATH=/app
ENV OPENROUTER_API_KEY=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

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]
