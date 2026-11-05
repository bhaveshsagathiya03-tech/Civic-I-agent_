FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-ml.txt ./
ARG INSTALL_ML=0
RUN if [ "$INSTALL_ML" = "1" ]; then pip install --no-cache-dir -r requirements-ml.txt; else pip install --no-cache-dir -r requirements.txt; fi
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
RUN mkdir -p /data/media
ENV MEDIA_DIR=/data/media
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
