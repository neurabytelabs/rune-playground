FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Clone RUNE repo at build time
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && git clone https://github.com/neurabytelabs/rune.git /opt/rune \
    && apt-get purge -y git && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

ENV RUNE_PATH=/opt/rune

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
