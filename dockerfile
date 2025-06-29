# Dockerfile for the Django app

# 1) Base image
FROM python:3.11-slim

# 2) Set up system deps
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
       build-essential \
       curl \
  && rm -rf /var/lib/apt/lists/*

# 3) Set working dir
WORKDIR /app

# 4) Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5) Copy project files
COPY . .

# 6) Collect static files
ENV DJANGO_SETTINGS_MODULE=guessai.settings
RUN python manage.py collectstatic --noinput

# 7) Expose port and run
EXPOSE 8000
CMD ["gunicorn", "guessai.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

