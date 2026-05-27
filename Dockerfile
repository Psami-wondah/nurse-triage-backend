FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=2 \
    TIMEOUT=120


WORKDIR /app

COPY requirements.txt /app

RUN pip3 install --upgrade pip

RUN pip3 install -r requirements.txt

COPY . /app

CMD ["sh", "-c", "gunicorn app:app --worker-class uvicorn.workers.UvicornWorker --bind ${HOST}:${PORT} --workers ${WORKERS} --timeout ${TIMEOUT} --access-logfile - --error-logfile -"]
