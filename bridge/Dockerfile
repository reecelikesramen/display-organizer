# Stage 1: Base image setup
FROM python:3.13-slim

# Prevents Python from writing .pyc files to disk and enables unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-root user and group for security
RUN addgroup --system appgroup && adduser --system --group appuser

# Set the working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code into the container
COPY ./app /app

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Expose port 8080 (Cloud Run expects this port)
EXPOSE 8080

# Use Gunicorn with Uvicorn workers to serve the FastAPI app.
# "app.main:app" tells Gunicorn to load the 'app' callable from app/main.py.
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "app.main:app"]
