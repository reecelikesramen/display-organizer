# Use the official Python image from Docker Hub
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app files into the container
COPY ./app /app

# Command to run Gunicorn with your FastAPI app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "main:app"]
