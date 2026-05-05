FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PYTHONPATH=/srv

WORKDIR /srv/uap

COPY requirements.txt /srv/uap/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . /srv/uap/

RUN addgroup --system adrion && adduser --system --ingroup adrion adrion
USER adrion

EXPOSE 8002

CMD ["python", "backend/api.py"]
