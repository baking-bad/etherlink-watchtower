ARG PYTHON_VERSION=3.12-slim-bookworm
ARG SOURCE_DIR=src
ARG APP_PATH=/opt/app
ARG APP_USER=watchtower

FROM python:${PYTHON_VERSION} AS builder-base

SHELL ["/bin/bash", "-exc"]

RUN apt-get update -qy \
 && apt-get install --no-install-recommends --no-install-suggests -qyy \
        # deps for building python deps
        build-essential \
        # pytezos deps
        libsodium-dev libgmp-dev pkg-config \
    \
    # cleanup \
 && apt-get clean \
 && rm -rf /tmp/* \
 && rm -rf /var/tmp/* \
 && rm -rf /root/.cache \
 && rm -rf /var/lib/apt/lists/*


FROM builder-base AS builder-production

ARG APP_PATH
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=0 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=$APP_PATH

COPY ["uv.lock", "pyproject.toml", "/lock/"]

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    cd /lock/ && \
	uv sync --locked --no-install-project --no-dev --no-cache && \
    cd $APP_PATH/lib/python3.12/site-packages && rm -rf \
    	nbclassic \
		debugpy \
		cytoolz \
		pygments \
		jedi \
		IPython \
		pyzmq.libs \
		notebook \
		jupyter_server \
		tornado \
		prompt_toolkit


FROM python:${PYTHON_VERSION} AS runtime-base

SHELL ["/bin/bash", "-exc"]

RUN apt-get update -qy \
 && apt-get install --no-install-recommends --no-install-suggests -qyy \
        # pytezos deps
        libsodium-dev libgmp-dev pkg-config \
    \
    # cleanup \
 && apt-get clean \
 && rm -rf /tmp/* \
 && rm -rf /var/tmp/* \
 && rm -rf /root/.cache \
 && rm -rf /var/lib/apt/lists/*

ARG APP_PATH
ENV PATH=$APP_PATH/bin:$PATH

WORKDIR $APP_PATH

ARG APP_USER
RUN useradd -ms /bin/bash $APP_USER


FROM runtime-base AS runtime

ARG APP_PATH
COPY --from=builder-production --chown=$APP_USER ["$APP_PATH", "$APP_PATH"]

ARG APP_USER
USER $APP_USER

ARG SOURCE_DIR
COPY --chown=$APP_USER $SOURCE_DIR/* .

CMD ["python", "-u", "app.py"]
