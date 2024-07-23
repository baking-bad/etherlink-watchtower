FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y curl gcc libgmp-dev libsodium-dev && \
    apt-get clean

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app
COPY . .

RUN poetry install --no-root --no-interaction --no-ansi

ENTRYPOINT ["poetry", "run"]
CMD ["python", "app.py"]

