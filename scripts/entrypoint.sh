#!/bin/sh
set -e

ROLE="${1:-api}"
shift || true

case "$ROLE" in
    api)
        exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8000}" "$@"
        ;;
    ingestion|producer|newsapi)
        exec python -m ingestion.newsapi_producer "$@"
        ;;
    gnews)
        exec python -m ingestion.gnews_producer "$@"
        ;;
    sink)
        exec python -m sink.mongo_sink "$@"
        ;;
    frontend|web|ui)
        cd /app/frontend
        exec node server.js "$@"
        ;;
    bash|sh|shell)
        exec /bin/sh "$@"
        ;;
    *)
        exec "$ROLE" "$@"
        ;;
esac
