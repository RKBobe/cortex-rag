# Use Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# Create the persistent directory
RUN mkdir -p chroma_db

# Expose the port
EXPOSE 8000

# Run the app (FORCE STANDARD ASYNCIO LOOP)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]
