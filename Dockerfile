FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy

WORKDIR /app

RUN apk add --no-cache tzdata libstdc++ \
    && apk add --no-cache --virtual .build-deps \
        build-base \
        cmake \
        pkgconf \
    && pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev && apk del .build-deps

COPY . .

CMD ["uv", "run", "python", "mcp_server.py", "--transport", "stdio"]
