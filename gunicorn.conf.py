"""
Gunicorn configuration file for AFS Assessment Framework
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
)

# Process naming
proc_name = "afs_assessment"

# Server mechanics
daemon = False
pidfile = "logs/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (for production with HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")


def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("worker received INT or QUIT signal")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info("worker received SIGABRT signal")


# Environment variable overrides
workers_env = os.environ.get('GUNICORN_WORKERS')
if workers_env:
    workers = int(workers_env)

timeout_env = os.environ.get('GUNICORN_TIMEOUT')
if timeout_env:
    timeout = int(timeout_env)

bind_env = os.environ.get('GUNICORN_BIND')
if bind_env:
    bind = bind_env

loglevel_env = os.environ.get('GUNICORN_LOG_LEVEL')
if loglevel_env:
    loglevel = loglevel_env

# Development settings
if os.environ.get('FLASK_ENV') == 'development':
    reload = True
    workers = 1
    loglevel = 'debug'