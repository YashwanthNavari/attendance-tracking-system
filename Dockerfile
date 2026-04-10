# Use the official pre-built face_recognition image
# This comes with dlib and face_recognition pre-installed
FROM ageitgey/face_recognition:latest

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
# We exclude dlib and face_recognition from here if they are already in the base
# But for safety, we'll keep them in requirements.txt and pip will see they are met
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Environment settings
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Expose the port
EXPOSE 10000

# Start application using Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
