# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Don’t generate .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Send stdout/stderr straight to terminal (no buffering)
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install gcc & libpq-dev so psycopg2 can compile, then clean up
COPY requirements.txt .
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libpq-dev \
 && pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-get purge -y --auto-remove gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy the rest of your code
COPY . .

# Expose the port your Django app will run on
EXPOSE 8000

# Run Gunicorn
CMD ["gunicorn", "guessai.wsgi:application", "--bind", "0.0.0.0:8000"]

