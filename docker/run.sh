#!/bin/sh

set -e

python manage.py collectstatic --no-input
python manage.py compilemessages

python manage.py migrate

exec "${@}"