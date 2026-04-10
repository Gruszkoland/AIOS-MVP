FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1

WORKDIR /app

COPY requirements-arbitrage.txt /app/requirements-arbitrage.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements-arbitrage.txt

RUN addgroup --system adrion && adduser --system --ingroup adrion adrion

COPY . /app

RUN chown -R adrion:adrion /app

USER adrion

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/api/arbitrage/status')" || exit 1

CMD ["waitress-serve", "--listen=0.0.0.0:8001", "wsgi:app"]
