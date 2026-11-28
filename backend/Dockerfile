FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY backend/requirements.lock.txt /app/requirements.lock.txt
RUN pip install -r requirements.lock.txt && useradd --create-home --uid 10001 app
COPY backend/app /app/app
COPY backend/alembic /app/alembic
COPY backend/alembic.ini backend/check_db.py /app/
RUN mkdir -p /app/storage && chown -R app:app /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
