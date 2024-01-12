# latest stable
ARG PYTHON_VERSION=latest
ARG NGINX_VERSION=1.25-alpine

FROM python:${PYTHON_VERSION} AS django
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PGSSLCERT /tmp/postgresql.crt
RUN mkdir -p /app
WORKDIR /app
COPY requirements/ ./requirements/
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements/prod.txt
COPY . .
RUN python manage.py collectstatic --clear
CMD ["gunicorn", "-c", "/app/app/gunicorn.py", "app.wsgi"]
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
