FROM python:3.12-slim AS build

ENV POETRY_VERSION=2.2.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Poetry
RUN pip install --no-cache-dir poetry==$POETRY_VERSION

WORKDIR /app

# Копируем только файлы зависимостей (кеш слоёв)
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости
RUN poetry install --no-root

# Копируем остальной код
COPY . .

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Копируем Python-site-packages и бинарники
COPY --from=build /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=build /usr/local/bin /usr/local/bin

# Копируем код проекта + .so
COPY --from=build /app /app

# (опционально) user без root
RUN useradd -m appuser && chown -R appuser /app
USER appuser

COPY . /app
WORKDIR /app

CMD ["gunicorn", "src.teltonika_http.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "4", \
     "-b", "0.0.0.0:8000", \
     "--timeout", "60"]
