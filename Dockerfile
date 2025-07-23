FROM python:3.11-slim

# Install system dependencies and Stockfish
RUN apt update && apt install -y stockfish

# Set working directory
WORKDIR /app

# Copy all project files into container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Flask uses
EXPOSE 8000

# Start the Flask app
CMD ["python", "main.py"]
