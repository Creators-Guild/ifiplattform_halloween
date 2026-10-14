# The server image: Django + Gunicorn, run by compose.prod.yml. Local
# development uses Dockerfile.dev instead. Guide:
# docs/operations/docker_server.md.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# A normal user instead of root.
RUN useradd --create-home app \
    && mkdir /app \
    && chown app:app /app
USER app
WORKDIR /app

COPY --chown=app:app ifiplatform/ ./

# The CSS/JS is built into the image and served by WhiteNoise, so each
# image carries exactly its own files. settings.py needs a secret key and
# a database name to load; collectstatic uses neither, so placeholders do.
# media/ and django_cache/ are created here so their volumes belong to app.
RUN DJANGO_SECRET_KEY=build-only DB_NAME=build-only \
        python manage.py collectstatic --noinput \
    && mkdir media django_cache

# Same settings as the old gunicorn.service: 3 workers, 30-minute timeout.
CMD ["gunicorn", "--workers", "3", "--timeout", "1800", "--bind", "0.0.0.0:8000", "ifiplatform_project.wsgi:application"]
