FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1

WORKDIR /app

COPY requirements-arbitrage.txt /app/requirements-arbitrage.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements-arbitrage.txt

COPY . /app

EXPOSE 8001

CMD ["waitress-serve", "--listen=0.0.0.0:8001", "wsgi:app"]
