# Use the full Python Bookworm image (more stable and includes build tools)
FROM python:3.10-bookworm

# Prevent apt-get from asking for user input
ENV DEBIAN_FRONTEND=noninteractive

# Update and install ONLY essential media libraries 
# (Most build tools like cmake and build-essential are already in Bookworm)
RUN apt-get update && apt-get install -y --no-install-recommends \
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
