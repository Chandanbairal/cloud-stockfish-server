# Use official Python image
FROM python:3.10-slim

# Install dependencies including Stockfish
RUN apt-get update && \
    apt-get install -y stockfish && \
    pip install flask chess

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Expose port
EXPOSE 8000

# Run app
CMD ["python", "main.py"]
