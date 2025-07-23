FROM python:3.11-slim

# Install dependencies and stockfish
RUN apt-get update && \
    apt-get install -y stockfish && \
    pip install flask python-chess && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Verify Stockfish installation
RUN stockfish --version

# Copy app code
COPY . /app
WORKDIR /app

EXPOSE 8000
CMD ["python", "main.py"]