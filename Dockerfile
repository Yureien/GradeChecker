FROM python:3.10-bullseye

LABEL name=grade-checker \
    version=0.1.0 \
    maintainer="Soham Sen <contact@sohamsen.me>"

EXPOSE 8000

ENV APP_ROOT=/opt/app \
    APP_USER=app

WORKDIR $APP_ROOT

RUN useradd -d $APP_ROOT -r $APP_USER

RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND="noninteractive" apt-get install --no-install-recommends -y \
    sqlite3 postgresql-client python3-opencv tesseract-ocr \
    libsm6 libxext6 ffmpeg libgl1-mesa-glx gettext \
    && apt-get clean

RUN pip install --no-cache-dir \
    "gunicorn[gevent]" \
    "uvicorn[standard]" \
    "psycopg2-binary"

COPY requirements.txt $APP_ROOT

RUN pip install --no-cache-dir -r requirements.txt

COPY . $APP_ROOT

RUN python $APP_ROOT/manage.py collectstatic --no-input

ENTRYPOINT ["docker/run.sh"]
CMD ["gunicorn", " -k uvicorn.workers.UvicornWorker", "-w 4", "-b :8000", "--log-file=-", "GradeChecker.asgi:application"]