# ---------- builder ----------
# Build the wheel in a scratch stage so the runtime image doesn't ship
# compilers or build deps.
FROM python:3.12-slim AS builder

WORKDIR /build

# Only what's needed to resolve and build the project.
COPY pyproject.toml README.md LICENSE.md /build/
COPY src /build/src

RUN pip install --no-cache-dir --upgrade pip build \
    && python -m build --wheel --outdir /build/dist

# ---------- runtime ----------
FROM python:3.12-slim AS runtime

# Un-buffered stdout so `docker logs` shows log lines as they happen.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Non-root user owns app + data dirs so the container does not run as root.
RUN useradd --create-home --shell /bin/bash --uid 1000 pychess \
    && mkdir -p /data \
    && chown -R pychess:pychess /data

WORKDIR /app
COPY --from=builder /build/dist/*.whl /tmp/
# Alembic reads migrations/ and alembic.ini from the filesystem, so we
# copy them into the image even though the Python package lives in the wheel.
COPY alembic.ini /app/
COPY migrations /app/migrations
RUN pip install --no-cache-dir /tmp/*.whl \
    gunicorn \
    gevent \
    gevent-websocket \
    && rm /tmp/*.whl \
    && chown -R pychess:pychess /app

USER pychess

ENV PYCHESS_DB_URL=sqlite:////data/matches.db \
    PYCHESS_AUTO_MIGRATE=1 \
    PYCHESS_CREATE_SCHEMA=0 \
    PYCHESS_SOCKETIO_ASYNC_MODE=gevent \
    PORT=8080

EXPOSE 8080
VOLUME ["/data"]

# Lightweight health check: /match/new exercises Flask routing without
# creating a match.
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8080\")}/match/new').read()"

# Gunicorn + gevent-websocket gives the Docker runtime a production-capable
# WebSocket server. Keep one worker unless a Socket.IO message queue is added.
CMD ["sh", "-c", "gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers 1 --bind 0.0.0.0:${PORT:-8080} --access-logfile - --error-logfile - 'pychess.web.app:create_app()'"]
