# Python 3.11
FROM python:3.11-slim

# working directory
WORKDIR /app

# install stockfish
RUN apt-get update && apt-get install -y \
    stockfish \
    && rm -rf /var/lib/apt/lists/*

# install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app
COPY app .

# port
EXPOSE 8000

# run
CMD ["python", "main.py"]