# latest stable
ARG PYTHON_VERSION=3.12.1-slim-bullseye

FROM python:${PYTHON_VERSION} AS django
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PGSSLCERT /tmp/postgresql.crt
RUN mkdir -p /app
WORKDIR /app
RUN apt-get update && apt-get install -y git gettext build-essential libffi-dev libpcre3-dev libpq-dev libssl-dev gettext
COPY requirements/ ./requirements/
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements/prod.txt
COPY . .
RUN python manage.py collectstatic --clear
RUN django-admin compilemessages
CMD ["gunicorn", "-c", "/app/app/gunicorn.py", "app.wsgi"]
