# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Prevent apt-get from asking for user input during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies with better resiliency
RUN apt-get update --fix-missing && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Environment settings
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Expose the port
EXPOSE 10000

# Start application
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
