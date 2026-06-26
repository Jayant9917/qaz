FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system novo && adduser --system --ingroup novo novo

COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --upgrade pip && python -m pip install .

USER novo

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "novo.main:app", "--host", "0.0.0.0", "--port", "8000"]
