FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN addgroup --system truecost && adduser --system --ingroup truecost truecost
COPY requirements.txt pyproject.toml README.md ./
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY broker ./broker
COPY scripts ./scripts
USER truecost
EXPOSE 8000 8010
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
