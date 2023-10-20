FROM python:3.11-slim-buster

RUN apt-get update \
    && apt-get -y install build-essential libpq-dev git curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /opt/app

ADD pyproject.toml .
ADD poetry.lock .
RUN poetry install

ADD bank bank


EXPOSE 8000
ENTRYPOINT ["poetry", "run"]
