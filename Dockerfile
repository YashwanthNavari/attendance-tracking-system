# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies required for face_recognition and opencv
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Environment variable to ensure the app processes don't buffer output
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on (Render uses 10000 by default for web services)
EXPOSE 10000

# Run gunicorn when the container launches
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
