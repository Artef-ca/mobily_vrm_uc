# Dockerfile

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy code only
COPY src /app/src
COPY app.py /app/


# No configs, no BQ env here – all provided at runtime
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
