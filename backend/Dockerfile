# Imazhi i backend-it FastAPI.
#
# Modeli i embeddings (sentence-transformers) shkarkohet në ekzekutimin
# e parë dhe ruhet te volumi `model_cache`, që rinisjet të mos e
# shkarkojnë përsëri.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models

WORKDIR /app

# Instalimi i varësive vjen para kopjimit të kodit, që ndryshimet e
# kodit të mos e rindërtojnë këtë shtresë.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
