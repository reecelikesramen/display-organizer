# Use the official Python image from Docker Hub
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app files into the container
COPY ./app /app

# Use Gunicorn with Uvicorn workers to serve the FastAPI app.
# "app.main:app" tells Gunicorn to load the 'app' callable from app/main.py.
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "app.main:app"]
