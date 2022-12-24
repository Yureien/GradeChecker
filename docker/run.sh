#!/bin/sh

set -e

python ./manage.py collectstatic --no-input
python ./manage.py compilemessages

python ./manage.py migrate

gunicorn --bind=0.0.0.0:8000 --access-logfile=- GradeChecker.asgi:application \
    --workers=4 -k uvicorn.workers.UvicornWorker
