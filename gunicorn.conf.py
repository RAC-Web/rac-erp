# gunicorn.conf.py - Gunicorn configuration for RAC HRMS
# Usage: gunicorn -c gunicorn.conf.py config.wsgi:application

import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
threads = 2
timeout = 120
keepalive = 5

# Logging
accesslog = "/var/log/rac-hrms/gunicorn-access.log"
errorlog = "/var/log/rac-hrms/gunicorn-error.log"
loglevel = "info"
