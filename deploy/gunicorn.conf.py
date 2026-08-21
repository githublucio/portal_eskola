"""Gunicorn settings for ESTVP Atauro portal (used behind Nginx)."""

import multiprocessing
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

bind = "127.0.0.1:8001"
workers = max(2, multiprocessing.cpu_count() * 2 + 1)
worker_class = "sync"
timeout = 30
graceful_timeout = 30
keepalive = 5
accesslog = "-"
errorlog = "-"
capture_output = True
chdir = str(BASE_DIR)
wsgi_app = "config.wsgi:application"
