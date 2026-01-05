"""Production entrypoint using Waitress WSGI server.
Run with: python -m waitress --host=0.0.0.0 --port=8000 wsgi:app
Or: python wsgi.py
"""
from waitress import serve
from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8562'))
    threads = int(os.getenv('WAITRESS_THREADS', '16'))
    connection_limit = int(os.getenv('WAITRESS_CONNECTION_LIMIT', '200'))
    channel_timeout = int(os.getenv('WAITRESS_CHANNEL_TIMEOUT', '300'))  # for long-lived SSE

    serve(
        app,
        host=host,
        port=port,
        threads=threads,
        connection_limit=connection_limit,
        channel_timeout=channel_timeout,
    )
